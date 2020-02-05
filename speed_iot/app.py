import requests
import json
from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates")


@app.route('/', methods=["GET"])
def get_root_page():
    """
    Renders the welcome page
    """
    return render_template('index.html')


"""
Calls used by the forms
"""
@app.route('/authenticate', methods=['POST'])
def authenticate():
    response, status = get_access_token()
    if status != 200:
        response['error'] = response
    return render_template("index.html", data=response)


@app.route('/check_service', methods=['POST'])
def check_address():
    """
    Check the services available for a certain address.
    If the address has fiber technology, send's an sms to a number
    """
    general_response = dict(access_token=request.form['accesstoken'], input=dict(
        client_id=request.form['clientid'], client_secret=request.form['clientsecret']))
    speed_response, status = call_speed_test_api()
    general_response['internet'] = speed_response
    if status == 200 and fiber_available(speed_response):
        sms_response, status = send_sms()
        general_response['sms'] = sms_response
    else:
        general_response['error'] = speed_response
    return render_template('index.html', data=general_response)


"""
API CALLS
"""


def get_access_token():
    url = "https://api-prd.kpn.com/oauth/client_credential/accesstoken"

    payload = dict(
        client_id=request.form["clientid"],
        client_secret=request.form["clientsecret"],
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = requests.post(
        url,
        params=dict(grant_type="client_credentials"),
        data=payload,
        headers=headers,
    )
    response = data.json()
    response['input'] = payload
    return response, data.status_code


def call_speed_test_api():
    """
    Call the speed test API with the parameters from request
    """
    url = "https://api-prd.kpn.com/network/kpn/internet-speed-check/offer"
    payload = {
        "service_address": {
            "house_number": request.form["house_number"],
            "zip_code": request.form["postcode"],
            "house_number_extension": request.form["house_extension"]
        }
    }
    headers = {"Authorization": f"Bearer {request.form['accesstoken']}",
               "Content-Type": "application/json", "accept": "application/json"}

    data = requests.post(url, data=json.dumps(payload), headers=headers)
    return data.json(), data.status_code


def send_sms():
    """
    Sends SMS using KPN SMS API
    """
     url = "https://api-prd.kpn.com/messaging/sms-kpn/v1/send"
    payload = {
        "sender": "KPN API",
        "messages": [{
            "mobile_number": "Receiver NUMBER",  # Change phone number
            "content": "Fiber detected!"  # update with your own message
        }]
    }
    headers = {
        "Authorization": f"Bearer {request.form['accesstoken']}", "Content-Type": "application/json"}

    data = requests.post(url, data=json.dumps(payload), headers=headers)
    return data.json(), data.status_code

def fiber_available(response):
    """
    Checks if fiber is in the input response
    """
    has_fiber = [True for tech in response['available_on_address']
                 ['technologies'] if tech['name'].lower() == "fiber"]
    return True if True in has_fiber else False


if __name__ == "__main__":
    app.run(port="5003", debug=True)
