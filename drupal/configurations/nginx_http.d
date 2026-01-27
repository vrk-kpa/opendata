server {
  listen 80 default_server;
  listen [::]:80 default_server;

  root /var/www/html;
  index index.php index.html;

  location / {
   try_files $uri /index.php?$query_string;
  }

  location ~ \.php$ {
    fastcgi_pass 127.0.0.1:9000;
    include fastcgi_params;
    fastcgi_intercept_errors on;
    fastcgi_index index.php;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    try_files $uri =404;
  }
}
