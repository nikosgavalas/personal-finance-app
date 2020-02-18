#!/bin/bash

#Run this script in the machine you want to deploy the apache
# apt install -y apache2 apache2-dev
# pip install django mod-wsgi

echo configuring apache...

cat << 'EOF' > /etc/apache2/sites-available/capital.conf
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
        DocumentRoot /var/www/html

        # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
        # error, crit, alert, emerg.
        # It is also possible to configure the loglevel for particular
        # modules, e.g.
        #LogLevel info ssl:warn

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        # For most configuration files from conf-available/, which are
        # enabled or disabled at a global level, it is possible to
        # include a line for only one particular virtual host. For example the
        # following line enables the CGI configuration for this host only
        # after it has been globally disabled with "a2disconf".
        #Include conf-available/serve-cgi-bin.conf

        #WSGIPythonHome /path/to/venv
        #WSGIPythonPath /path/to/mysite.com

        #Alias /robots.txt /path/to/mysite.com/static/robots.txt
        #Alias /favicon.ico /path/to/mysite.com/static/favicon.ico

        #Alias /media/ /path/to/mysite.com/media/
        Alias /static/ /path/to/mysite.com/static/

        <Directory /path/to/mysite.com/static>
                Require all granted
        </Directory>

        #<Directory /path/to/mysite.com/media>
        #       Require all granted
        #</Directory>

        WSGIScriptAlias / /path/to/mysite.com/mysite/wsgi.py

        <Directory /path/to/mysite.com/mysite>
                <Files wsgi.py>
                        Require all granted
                </Files>
        </Directory>

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
EOF

a2ensite capital



