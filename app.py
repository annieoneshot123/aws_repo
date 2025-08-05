import os
import uuid
import json
import boto3
from flask import Flask, render_template, request, redirect

# --- CONFIGURATION (To be updated in Part 7) ---
# Name of the S3 Bucket you will create
S3_BUCKET = "YOUR_S3_BUCKET_NAME" 
# Name of the Secret you created in Secrets Manager
SECRET_NAME = "photoshare/db/credentials"
# AWS services region
AWS_REGION = "us-east-1" 
# URL of the CloudFront Distribution you will create
CLOUDFRONT_URL = "https://YOUR_CLOUDFRONT_URL" 
# -----------------------------------------------

app = Flask(__name__)

# Initialize clients for AWS SDK (Boto3)
session = boto3.session.Session()
secrets_client = session.client(service_name='secretsmanager', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)

def get_db_credentials():
    """Function to get database credentials from AWS Secrets Manager."""
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

# Get credentials once when application starts
db_creds = get_db_credentials()
# Replace pymysql with more compatible library like mysql-connector-python
import mysql.connector

def get_db_connection():
    """Function to create database connection."""
    try:
        conn = mysql.connector.connect(
            host=db_creds['host'],
            user=db_creds['username'],
            password=db_creds['password'],
            database=db_creds['dbname']
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e

@app.route('/')
def index():
    """Homepage for uploading images."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handle image upload process."""
    file = request.files.get('photo')
    if not file:
        return "No file uploaded", 400

    # Generate unique filename
    filename = f"{uuid.uuid4()}_{file.filename}"
    
    try:
        # Change 1: Upload file directly to S3 instead of saving locally
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )

        # Save metadata to RDS
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO photos (filename, uploaded_at) VALUES (%s, NOW())"
            cursor.execute(sql, (filename,))
        conn.commit()
        conn.close()

    except Exception as e:
        return f"An error occurred: {e}", 500

    return redirect('/gallery')

@app.route('/gallery')
def gallery():
    """Page to display photo gallery."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT filename FROM photos ORDER BY uploaded_at DESC")
            photos = cursor.fetchall()
        conn.close()
        
        # Change 2: Create image URLs from CloudFront instead of local server
        urls = [f"{CLOUDFRONT_URL}/{photo[0]}" for photo in photos]
        return render_template('gallery.html', photos=urls)
    except Exception as e:
        return f"An error occurred: {e}", 500

# Change 3: Completely remove /uploads/<filename> endpoint as CloudFront handles this
# It is no longer needed.

if __name__ == '__main__':
    # Run on port 8000 during development, Gunicorn will manage port in production
    app.run(host='0.0.0.0', port=8000, debug=True)