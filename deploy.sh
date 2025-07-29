#!/bin/bash

# Exit on any error
set -e

echo "Starting deployment script..."

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    nginx \
    postgresql-client \
    git \
    certbot \
    python3-certbot-nginx

# Create application directory
sudo mkdir -p /var/www/bottit
sudo chown $USER:$USER /var/www/bottit

# Clone repository (if not already present)
if [ ! -d "/var/www/bottit/.git" ]; then
    git clone https://github.com/your-username/bottit.git /var/www/bottit
fi

cd /var/www/bottit

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Please edit .env file with your settings"
fi

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (interactive)
echo "Creating superuser..."
python manage.py createsuperuser

# Set up Nginx configuration
sudo tee /etc/nginx/sites-available/bottit << EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location /static/ {
        alias /var/www/bottit/staticfiles/;
    }

    location /media/ {
        alias /var/www/bottit/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/bottit /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Create systemd service for Gunicorn
sudo tee /etc/systemd/system/bottit.service << EOF
[Unit]
Description=Bottit Django application
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/bottit
Environment="PATH=/var/www/bottit/venv/bin"
ExecStart=/var/www/bottit/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 bottit.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable services
sudo systemctl daemon-reload
sudo systemctl start bottit
sudo systemctl enable bottit
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "Deployment completed!"
echo "Don't forget to:"
echo "1. Edit /var/www/bottit/.env with your settings"
echo "2. Update server_name in /etc/nginx/sites-available/bottit"
echo "3. Set up SSL with: sudo certbot --nginx -d your-domain.com"
echo "4. Restart services after changes: sudo systemctl restart bottit nginx"
