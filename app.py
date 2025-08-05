import os
import uuid
import json
import boto3
from flask import Flask, render_template, request, redirect

# --- CẤU HÌNH ĐÃ THAY ĐỔI ---
S3_BUCKET = "photoshare-app-147"
SECRET_NAME = "photoshare/db/credentials"
AWS_REGION = "us-east-1"
# THAY ĐỔI 1: Xóa biến CLOUDFRONT_URL vì không còn sử dụng
# ---------------------------------------------

app = Flask(__name__)

# Khởi tạo clients cho AWS SDK (Boto3)
session = boto3.session.Session()
secrets_client = session.client(service_name='secretsmanager', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)

def get_db_credentials():
    """Hàm lấy thông tin đăng nhập DB từ AWS Secrets Manager."""
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

db_creds = get_db_credentials()
import mysql.connector

def get_db_connection():
    """Hàm tạo kết nối tới database."""
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
    """Trang chủ để upload ảnh."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Xử lý việc upload ảnh."""
    file = request.files.get('photo')
    if not file:
        return "No file uploaded", 400

    filename = f"{uuid.uuid4()}_{file.filename}"
    
    try:
        # THAY ĐỔI 2: Thêm quyền 'public-read' khi upload file lên S3
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            filename,
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )

        # Lưu metadata vào RDS
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
    """Trang hiển thị bộ sưu tập ảnh."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT filename FROM photos ORDER BY uploaded_at DESC")
            photos = cursor.fetchall()
        conn.close()
        
        # THAY ĐỔI 3: Tạo URL trực tiếp đến S3 object thay vì qua CloudFront
        urls = [f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{photo[0]}" for photo in photos]
        return render_template('gallery.html', photos=urls)
    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
