#!/bin/bash


[ "$UID" -eq 0 ] || { echo run as root.; exit 1; }

BASE_DIR="$(cd "$(dirname "$0")"; pwd)"
DEPL_DIR=/mnt/storage/srv/capital

PIP_REQS=$BASE_DIR/requirements_prod.txt
export DJANGO_SETTINGS_MODULE="capital.settings_prod"

echo installing dependencies...
apt install -y apache2 apache2-dev python3 python3-pip python3-venv

echo installing sources...
rm -rf $DEPL_DIR/capital
cp -a "$BASE_DIR/capital" $DEPL_DIR
chown -R www-data:www-data $DEPL_DIR/capital

echo -n "installing the python virtual environment..."
if [[ ! -d $DEPL_DIR/venv ]]; then
    (cd $DEPL_DIR; python3 -m venv venv)
    (source $DEPL_DIR/venv/bin/activate; pip install wheel; pip install -r $BASE_DIR/requirements_prod.txt; mod_wsgi-express module-config > /etc/apache2/mods-available/wsgi.load)
    echo OK
else
    echo "already present."
fi
chown -R www-data:www-data $DEPL_DIR/venv

ADMIN_DIR=$(source $DEPL_DIR/venv/bin/activate; python -c "import django.contrib.admin as _; print(_.__path__[0])")

echo -n "configuring database..."
mkdir -p $DEPL_DIR/db
touch $DEPL_DIR/db/prod.sqlite3
chown -R www-data:www-data $DEPL_DIR/db
(source $DEPL_DIR/venv/bin/activate; cd $DEPL_DIR/capital; python manage.py migrate)

echo configuring apache...
cat << EOF > /etc/apache2/sites-available/capital.conf
<VirtualHost *:80>
    ServerName capital.nickgavalas.com
    ServerAdmin webmaster@localhost

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined

    # Enforce https
    RewriteEngine on
    RewriteCond %{SERVER_NAME} =capital.nickgavalas.com
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

EOF

cat << EOF > /etc/apache2/sites-available/capital-le-ssl.conf
<IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerName capital.nickgavalas.com
        ServerAdmin webmaster@localhost

        ErrorLog \${APACHE_LOG_DIR}/error.log
        CustomLog \${APACHE_LOG_DIR}/access.log combined

        WSGIScriptAlias / ${DEPL_DIR}/capital/capital/wsgi.py
        <Directory ${DEPL_DIR}/capital/capital>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>

        Alias /robots.txt ${DEPL_DIR}/capital/app/static/app/robots.txt
        Alias /favicon.ico ${DEPL_DIR}/capital/app/static/app/favicon.ico

        Alias /static/app/ ${DEPL_DIR}/capital/app/static/app/
        <Directory ${DEPL_DIR}/capital/app/static/app>
            Require all granted
        </Directory>

        Alias /static/admin/ ${ADMIN_DIR}/static/admin/
        <Directory ${ADMIN_DIR}/static/admin/>
            Require all granted
        </Directory>

        SSLCertificateFile /etc/letsencrypt/live/capital.nickgavalas.com/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/capital.nickgavalas.com/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>
</IfModule>

EOF

a2ensite capital
a2ensite capital-le-ssl
a2enmod wsgi

systemctl restart apache2
