from flask import Flask, render_template, request, redirect, session
import psycopg2

app = Flask(__name__, static_folder='static')
app.secret_key = "secured"

def databse_connection():
    connection = psycopg2.connect(
        dbname = "SchoolFeesCollection",
        user = "postgres",
        password = "secured",
        host = "localhost",
        port = 5432
    )
    return connection
 
#_______________**** LOGIN ****____________________
@app.route('/', methods = ['GET', 'POST'] )
def login():
    if request.method == 'POST':
        username = request.form ['username']
        password = request.form ['password']

        connection = databse_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user_details WHERE mobile_no = %s AND pwd = %s",(username,password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', message = 'Invalid Credentials')
    else:
        return render_template('login.html')
    
#________________**** DASHBOARD ****______________
@app.route('/dashboard')
def dashboard():
    if 'username' in session: 
        username = session['username']
        connection = databse_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT parent_name FROM user_details WHERE mobile_no = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            user_name = user[0]
        else:
            user_name = "Unknown"

        connection = databse_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT school_details.id, school_details.name FROM school_details JOIN student_details ON school_details.id = student_details.school_id JOIN user_details ON CAST(user_details.mobile_no AS bigint) = student_details.parent_mobile1 WHERE user_details.mobile_no = %s",(username,))
        schools = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('dashboard.html', username = user_name, schools = schools)
    else:
        return redirect ('/')
    
#___________________**** DISPLAY ****__________________
@app.route('/display/<school_id>')
def display(school_id):
    if 'username' in session:
        username = session['username']
        connection = databse_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT name from school_details where id = %s",(school_id,))
        school_name = cursor.fetchone()[0]
        cursor.execute("SELECT student_id, full_name, garde_id, section_id, date_of_birth, fees, due_date FROM student_details WHERE parent_mobile1 =%s AND school_id = %s", (username, school_id))
        students = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('display.html', school_name = school_name, students = students)
    else:
        return redirect('/')
    

#___________________**** RUN ****______________________

if __name__ == '__main__':
    app.run(debug=True)

        
