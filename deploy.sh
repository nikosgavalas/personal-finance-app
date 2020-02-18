#!/bin/bash

#Run this script in the machine you want to deploy the apache

[ "$UID" -eq 0 ] || { echo run as root.; exit 1; } #|| exec sudo "$0" "$@"

BASE_DIR="$(cd "$(dirname "$0")"; pwd)"
export DJANGO_SETTINGS_MODULE="capital.prod_settings"

echo installing dependencies...
# apt install -y apache2 apache2-dev python3-venv

echo installing sources...
rm -rf /srv/capital
cp -r "$BASE_DIR/capital" /srv
chown -R www-data:www-data /srv/capital

echo -n "installing the python virtual environment..."
if [ ! -d /srv/venv ]; then
    (cd /srv; python3 -m venv venv)
    (source /srv/venv/bin/activate; pip3 install django mod-wsgi; mod_wsgi-express module-config > /etc/apache2/mods-available/wsgi.load)
    echo OK
else
    echo "already present."
fi
chown -R www-data:www-data /srv/venv

ADMIN_DIR=$(source /srv/venv/bin/activate; python3 -c "import django.contrib.admin as _; print(_.__path__[0])")

echo -n "configuring database..."
mkdir -p /srv/db
touch /srv/db/prod.sqlite3
chown -R www-data:www-data /srv/db
(source /srv/venv/bin/activate; cd /srv/capital; python3 manage.py migrate)

echo configuring apache...
cat << EOF > /etc/apache2/sites-available/capital.conf
<VirtualHost *:80>
        # The ServerName directive sets the request scheme, hostname and port that
        # the server uses to identify itself. This is used when creating
        # redirection URLs. In the context of virtual hosts, the ServerName
        # specifies what hostname must appear in the request's Host: header to
        # match this virtual host. For the default virtual host (this file) this
        # value is not decisive as it is used as a last resort host regardless.
        # However, you must set it for any further virtual host explicitly.
        #ServerName www.example.com

        ServerAdmin webmaster@localhost
        #DocumentRoot /var/www/html

        # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
        # error, crit, alert, emerg.
        # It is also possible to configure the loglevel for particular
        # modules, e.g.
        #LogLevel info ssl:warn

        ErrorLog \${APACHE_LOG_DIR}/error.log
        CustomLog \${APACHE_LOG_DIR}/access.log combined

        # For most configuration files from conf-available/, which are
        # enabled or disabled at a global level, it is possible to
        # include a line for only one particular virtual host. For example the
        # following line enables the CGI configuration for this host only
        # after it has been globally disabled with "a2disconf".
        #Include conf-available/serve-cgi-bin.conf

        #WSGIPythonHome /srv/venv
        #WSGIPythonPath /srv/capital

        WSGIScriptAlias / /srv/capital/capital/wsgi.py

        <Directory /srv/capital/capital>
                <Files wsgi.py>
                        Require all granted
                </Files>
        </Directory>

        #Alias /robots.txt /path/to/mysite.com/static/robots.txt
        #Alias /favicon.ico /path/to/mysite.com/static/favicon.ico

        #Alias /media/ /path/to/mysite.com/media/
        Alias /static/app/ /srv/capital/app/static/app/
        <Directory /srv/capital/app/static/app>
                Require all granted
        </Directory>

        Alias /static/admin/ ${ADMIN_DIR}/static/admin/
        <Directory ${ADMIN_DIR}/static/admin/>
                Require all granted
        </Directory>

        #<Directory /path/to/mysite.com/media>
        #       Require all granted
        #</Directory>

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
EOF

a2ensite capital
a2enmod wsgi
systemctl reload apache2

echo "TODO: install crontab to backup the database"

