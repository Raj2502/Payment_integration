# app.py
from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import shortuuid
import requests
import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from datetime import datetime

app = Flask(__name__)

# Flask-Mail configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your Gmail email
app.config['MAIL_PASSWORD'] = 'your_password'  # Replace with your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'  # Replace with your Gmail email

mail = Mail(app)

def calculate_sha256_string(input_string):
    sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    sha256.update(input_string.encode('utf-8'))
    return sha256.finalize().hex()

@app.route("/", methods=['GET'])
def welcome():
    return render_template('display.html', school_name="Your School", students=[["1", "John Doe", "Grade 10", "Section A", "2002-01-01", "100", "2024-02-29"]])

@app.route("/pay", methods=['GET'])
def pay():
    student_id = request.args.get('studentId')
    fees = request.args.get('fees')
    amount = request.args.get('amount')

    if not amount or not amount.isdigit():
        return render_template('display.html', school_name="Your School", students=[["1", "John Doe", "Grade 10", "Section A", "2002-01-01", "100", "2024-02-29"]])

    MAINPAYLOAD = {
        "merchantId": "PGTESTPAYUAT",
        "merchantTransactionId": shortuuid.uuid(),
        "merchantUserId": student_id,
        "amount": int(amount) * 100,
        "redirectUrl": "http://127.0.0.1:5000/return-to-me",
        "redirectMode": "POST",
        "callbackUrl": "http://127.0.0.1:5000/return-to-me",
        "mobileNumber": "9999999999",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }

    INDEX = "1"
    ENDPOINT = "/pg/v1/pay"
    SALTKEY = "099eb0cd-02cf-4e2a-8aca-3e6c6aff0399"

    base64String = base64.b64encode(json.dumps(MAINPAYLOAD).encode('utf-8')).decode('utf-8')
    mainString = base64String + ENDPOINT + SALTKEY
    sha256Val = calculate_sha256_string(mainString)
    checkSum = sha256Val + '###' + INDEX

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checkSum,
        'accept': 'application/json',
    }
    json_data = {
        'request': base64String,
    }
    response = requests.post('https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay', headers=headers, json=json_data)
    responseData = response.json()
    return redirect(responseData['data']['instrumentResponse']['redirectInfo']['url'])

@app.route("/return-to-me", methods=['POST'])
def payment_return():
    INDEX = "1"
    SALTKEY = "099eb0cd-02cf-4e2a-8aca-3e6c6aff0399"

    form_data = request.form
    form_data_dict = dict(form_data)

    if 'transactionId' in form_data_dict:
        transaction_id = form_data_dict["transactionId"]

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        request_url = f'https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/status/PGTESTPAYUAT/{transaction_id}'
        sha256_payload_string = f'/pg/v1/status/PGTESTPAYUAT/{transaction_id}{SALTKEY}'
        sha256_val = calculate_sha256_string(sha256_payload_string)
        checksum = f'{sha256_val}###{INDEX}'

        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': transaction_id,
            'accept': 'application/json',
        }
        
        response = requests.get(request_url, headers=headers)
        checkout_response = response.json()

        payment_details = {
            "amount": checkout_response['data']['amount'],
            # Add other payment details as needed
        }

        # Send invoice via email
        send_invoice('your_email@gmail.com', payment_details)  # Change this to the user's email

        return render_template('successful_page.html', form_data=form_data_dict, checkout_response=checkout_response,
                               transaction_id=transaction_id, current_datetime=formatted_datetime, payment_details=payment_details)

    return render_template('display.html', school_name="Your School", students=[["1", "John Doe", "Grade 10", "Section A", "2002-01-01", "100", "2024-02-29"]])

def send_invoice(email, payment_details):
    subject = 'Invoice for Your Recent Payment'
    body = f"Thank you for your payment! Here is your invoice:\n\nAmount: {payment_details['amount']}\n"
    # Add other payment details to the email body as needed

    message = Message(subject=subject, recipients=[email], body=body)
    
    try:
        mail.send(message)
        print("Invoice sent successfully!")
    except Exception as e:
        print(f"Error sending invoice: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
