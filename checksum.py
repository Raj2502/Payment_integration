# LIB
import jsons
import base64
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from flask import Flask, render_template, request, redirect
import shortuuid

app = Flask(__name__)

# HELPER FUNCTION
def calculate_sha256_string(input_string):
    sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    sha256.update(input_string.encode('utf-8'))
    return sha256.finalize().hex()

def base64_encode(input_dict):
    json_data = jsons.dumps(input_dict)
    data_bytes = json_data.encode('utf-8')
    return base64.b64encode(data_bytes).decode('utf-8')

# MAIN APP ROUTES
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

    base64String = base64_encode(MAINPAYLOAD)
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
        request_url = f'https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/status/PGTESTPAYUAT/{form_data_dict["transactionId"]}'
        sha256_payload_string = f'/pg/v1/status/PGTESTPAYUAT/{form_data_dict["transactionId"]}{SALTKEY}'
        sha256_val = calculate_sha256_string(sha256_payload_string)
        checksum = f'{sha256_val}###{INDEX}'

        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': form_data_dict['transactionId'],
            'accept': 'application/json',
        }
        
        response = requests.get(request_url, headers=headers)
        checkout_response = response.json()

        return render_template('successful_page.html', form_data=form_data_dict, checkout_response=checkout_response)

    return render_template('display.html', school_name="Your School", students=[["1", "John Doe", "Grade 10", "Section A", "2002-01-01", "100", "2024-02-29"]])

# Start The App
if __name__ == '__main__':
    app.run(debug=True)
