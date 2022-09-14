# Parley-it
##### API to simply perform an advance and schedule it for 12 weeks.


## Introduction
This API uses two other API calls (perform_transaction, download_report) for credits a customer an then debit him in 12 pays.


## Technologies
Django - 4.1.1 <br />
djangorestframework - 3.13.1


## API Calls
#### 1. POST: perform_transacrion(src_bank_account, dst_bank_account, amount, direction):
This call makes a transaction and returns the transaction id.

#### 2. GET: download_report():
This call downloads a report of the transaction that done in the last 5 days.

### These two calls doesn't exist in this project, We just make a FAKE version of them just for testing the perform_advance call.
<br />

#### 3. POST: perform_advance(dst_bank_account, amount):
This call credits the customer (dst_bank_account) with the amount, and then debits him for 12 weeks with amount/12 once a week,<br /> 
While a fail debit moves to be done in a week from the last payment. <br />
If the payment of the week from the last failed the details of this payment will be saved in the DB as failed transaction so it can be done again later.<br />
Furthermore, all the data about the transactions save in the DB, including the payments that failed and movedt to the end of the repayment plan.


## Launch
#### 1. Clone the git repository

#### 2. Install the requirements
 `cd <Parley-it folder>` <br />
  `pip install -r requirements.txt`

#### 2. Run the server
 `python manage.py runserver`
 
#### 3. Register/Login with existing user or admin
  Open Postman or any other API Platform and make a POST request.<br /><br />
 for register: <br />
 `http://127.0.0.1:8000/register/` <br />
 Add to the body a json with "username", "password" and "password2". <br />
 `{
    "username": "user1",
    "password": "qawsed12345",
    "password2": "qawsed12345"
}`
 <br /><br /> or <br /><br />
 for login: <br />
 `http://127.0.0.1:8000/api-token-auth/` <br />
  Add to the body a json with "username" and "password". <br />
  `{
    "username": "admin",
    "password": "123456"
}`
  
  #### For testing the API there are admin and one more user ("user1") already registered to the server, <br /> The file "user_details.json" includes all their details for runnung the API.
  
#### 4. Make the call
  Make a POST request <br />
  `http://127.0.0.1:8000/perform_advance/` <br />
  Add to the body a json with "dst_bank_account" and "amount", <br />
  `{
    "dst_bank_account": "1000000000",
    "amount": 240
}` <br />
  Also add to the header a "Authorization" key with a value of "Token <logged_in_user_token>". <br /><br />
  Example: <br />
  ![image](https://user-images.githubusercontent.com/111747736/190264081-354a8407-46fb-45f1-a0e8-68cf105c61ae.png)
  <br />
  `Key: Authorization`<br />
  `Value: Token 1853cefa6e6149ba2984ea16246ebf6f2a85e26d`

 <br />
 
  Then the system will credit the user with the amount, <br />
  if the credit will success the system will debit the user in the next 12 weeks with amount/12.
 
 
## More Features
#### 1. Rerun undone scheduled transactions
  Transactions that had scheduled to 12 weeks further but didn't done because the server stopped will rerun from the point they stopped when the server will start runnung again.

#### 2. Permissions:
  Only admin user or the user itself can use the perform_advance call.
