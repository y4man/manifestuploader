from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from xml.etree.ElementTree import Element, SubElement, tostring
from sqlalchemy.orm import relationship
from sqlalchemy.orm import joinedload
import xml.etree.ElementTree as ET
from xml.dom import minidom
from sqlalchemy import Numeric
import pandas as pd
from datetime import datetime as dt
from sqlalchemy import func
import io
from flask_migrate import Migrate


app = Flask(__name__)
app.static_folder = 'assets'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/aeropost'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'y321'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class CSVData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manifest_id = db.Column(db.Integer, db.ForeignKey('manifest.id'), nullable=False)
    consignee = db.Column(db.String(50), nullable=False)
    description_code = db.Column(db.String(50), nullable=False)
    tin_number = db.Column(db.String(50), nullable=False)
    values_str_list = db.Column(db.String(50), nullable=False)
    traffic_code = db.Column(db.String(50), nullable=False)
    mawb = db.Column(db.String(50), nullable=False)
    weight_lbs = db.Column(db.String(50), nullable=False)
    freight_price = db.Column(Numeric(precision=10, scale=2), nullable=False)
    insurance_price = db.Column(Numeric(precision=10, scale=2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    qty_unit = db.Column(db.String(50), nullable=True)  


class Manifest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dateOfEntry = db.Column(db.Date, nullable=False)
    airLine = db.Column(db.String(50), nullable=False)
    flightNumber = db.Column(db.String(50), nullable=False)
    carrier = db.Column(db.String(50), nullable=False)
    carriername = db.Column(db.String(50), nullable=False)
    shippingport = db.Column(db.String(50), nullable=False)
    billnumber = db.Column(db.String(50), nullable=False)
    pkgcount = db.Column(db.String(50), nullable=False)
    pkgtype = db.Column(db.String(50), nullable=False)
    grosswt = db.Column(db.String(50), nullable=False)
    grosswtunit = db.Column(db.String(50), nullable=False)
    grossvol = db.Column(db.String(50), nullable=False)
    grossvolunit = db.Column(db.String(50), nullable=False)
    ffname = db.Column(db.String(50), nullable=False)
    ffaddress = db.Column(db.String(50), nullable=False)
    ffcity = db.Column(db.String(50), nullable=False)
    ffstate = db.Column(db.String(50), nullable=False)
    ffcountry = db.Column(db.String(50), nullable=False)
    ffzip = db.Column(db.String(50), nullable=False)
    netcost = db.Column(db.String(50), nullable=False)
    netfreight = db.Column(db.String(50), nullable=False)
    arrivaldate = db.Column(db.String(50), nullable=False)
    departuredate = db.Column(db.String(50), nullable=False)
    dischargeport = db.Column(db.String(50), nullable=False)
    tod = db.Column(db.String(50), nullable=False)
    categoryofgoods = db.Column(db.String(50), nullable=False)
    regime = db.Column(db.String(50), nullable=False)
    contents = db.Column(db.String(50), nullable=False)
    # Add a relationship with CSVData
    csv_data_entries = relationship('CSVData', backref='manifest', cascade='all, delete-orphan')
        # Add a new field for transportation
    transportation = db.Column(db.String(10), nullable=True)
    

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    def get_id(self):
        return (self.id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create the tables
with app.app_context():
    db.create_all()


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=dt.utcnow)
    description = db.Column(db.String(255))

    def __init__(self, description, user_id=None):
        self.user_id = user_id
        self.description = description

    @staticmethod
    def log_activity(description, user_id=None):
        log_entry = ActivityLog(description=description, user_id=user_id)
        db.session.add(log_entry)
        db.session.commit()

    @staticmethod
    def get_activity_logs():
        return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()


# Create tables in the database
with app.app_context(): 
    db.create_all()

# @app.route('/')
# @login_required
# def homepage():
#     return redirect(url_for('login'))


@app.route("/register_key_authentication", methods=["GET", "POST"])
def reg_auth():
    if request.method == 'POST':
        register_key_authentication = request.form['reg-key']
        if register_key_authentication == "39a78212930eb099ec374fe32067ba4D5183b6dca1ee032b10dba068d18abfe4":
            flash("Congratulations! Authentication is Completed")
            return redirect(url_for('register'))
        else:
            flash("Invalid Key")
            return render_template('registration_auth.html')  # Corrected typo here
    return render_template('registration_auth.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)  # Ensure the user object is an instance of UserMixin
            flash('Login successful', 'success')
            return redirect(url_for('index'))  # Change this line

        flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        username = request.form['username']
        password = request.form['password']
      
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed. {e}', 'danger')

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@login_required
def index():
    # Check if the user is logged in
    if not current_user.is_authenticated:
        # If not logged in, you can redirect them to the login page or handle it in another way
        return redirect(url_for('login'))  # Adjust 'login' to the actual login route in your app

    # If logged in, proceed with the view logic
    items = Manifest.query.all()
    return render_template('manifests.html', items=items)


@app.route('/activity_history')
@login_required
def activity_history():
    log_description = f"Manifest submitted by {current_user.username}" if current_user.is_authenticated else "Manifest submitted"
    ActivityLog.log_activity(description=log_description)

    flash('Manifest successfully submitted', 'success')
    return redirect(url_for('view_activity_logs'))


@app.route('/view_activity_logs')
@login_required
def view_activity_logs():
    activity_logs = ActivityLog.get_activity_logs()
    return render_template('history.html', activity_logs=activity_logs)


def read_and_extract_data(csv_file, selected_headers):
    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Filter only the columns specified in selected_headers
    df_selected = df[selected_headers]

    # Convert DataFrame to a dictionary
    header_data = df_selected.to_dict(orient='list')

    # Extract data into separate variables
    consignee = header_data.get('Consignee', [])
    description_code = header_data.get('Description Code', [])
    tin_number = header_data.get('TinNumber', [])
    values_str_list = header_data.get('Value', [])
    traffic_code = header_data.get('Traffic Code', [])
    mawb = header_data.get('MAWB', [])
    weight_lbs = header_data.get('Weight Lbs', [])
    pieces = header_data.get('Pieces', [])

    return consignee, description_code, tin_number, values_str_list, traffic_code, mawb, weight_lbs, pieces


@app.context_processor
def inject_username():
    # Make 'username' available to all templates
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
        return dict(username=user.username)
    return dict(username=None)


@app.route('/manifest', methods=['GET', 'POST'])
@login_required
def manifest_form():
    if request.method == 'POST':
        # Retrieve form data from the request object
        dateOfEntry = request.form.get('doe')
        airLine = request.form.get('vesselcode')
        flightNumber = request.form.get('voyogeno')
        carrier = request.form.get('carrier')
        carriername = request.form.get('carriername')
        shippingport = request.form.get('shippingport')
        billnumber = request.form.get('billnumber')
        pkgcount = request.form.get('pkgcount')
        pkgtype = request.form.get('pkgtype')
        grosswt = request.form.get('grosswt')
        grosswtunit = request.form.get('grosswtunit')
        grossvol = request.form.get('grossvol')
        grossvolunit = request.form.get('grossvolunit')
        ffname = request.form.get('ffname')
        ffaddress = request.form.get('ffaddress')
        ffcity = request.form.get('ffcity')
        ffstate = request.form.get('ffstate')
        ffcountry = request.form.get('ffcountry')
        ffzip = request.form.get('ffzip')
        netcost = request.form.get('netcost')
        netfreight = request.form.get('netfreight')
        arrivaldate = request.form.get('arrivaldate')
        departuredate = request.form.get('departuredate')
        dischargeport = request.form.get('dischargeport')
        tod = request.form.get('tod')
        categoryofgoods = request.form.get('categoryofgoods')
        regime = request.form.get('regime')
        contents = request.form.get('contents')
        csv_file = request.files['csv_file']
        transportation = request.form.get('transportation')

        # Process uploaded CSV file
        if 'csv_file' in request.files:
            csv_file = request.files['csv_file']
            selected_headers = ['Consignee', 'Description Code', 'TinNumber', 'Value', 'Traffic Code', 'MAWB', 'Weight Lbs', 'Pieces']
            consignee, description_code, tin_number, values_str_list, traffic_code, mawb, Weight_Lbs, pieces = read_and_extract_data(csv_file, selected_headers)

            
            # Convert netfreight to float
            netfreight_float = float(request.form.get('netfreight'))

            # Create a new manifest record
            manifest = Manifest(dateOfEntry=dateOfEntry, airLine=airLine, flightNumber=flightNumber, carrier=carrier, regime=regime,
                                carriername=carriername, shippingport=shippingport, billnumber=billnumber, pkgcount=pkgcount,
                                pkgtype=pkgtype, grosswt=grosswt, grosswtunit=grosswtunit, grossvol=grossvol, contents=contents,
                                grossvolunit=grossvolunit, ffname=ffname, ffaddress=ffaddress, ffcity=ffcity, ffstate=ffstate,
                                ffcountry=ffcountry, ffzip=ffzip, netcost=netcost, netfreight=netfreight, arrivaldate=arrivaldate,
                                departuredate=departuredate, dischargeport=dischargeport, tod=tod, categoryofgoods=categoryofgoods,transportation=transportation)

            # Commit the Manifest entry
            db.session.add(manifest)
            db.session.commit()

            # Create CSVData entries and associate them with the manifest

            for consignee_val, description_code_val, tin_number_val, values_str_list_val, traffic_code_val, mawb_val, weight_lbs_val, piece_val in zip(consignee, description_code, tin_number, values_str_list, traffic_code, mawb, Weight_Lbs, pieces):

                product_units = {
                '8415.90.00': 'NO',
                '8414.20.00': 'NO',
                '8531.10.00': 'NO',
                '4820.50.00': 'KG',
                '8509.80.00': 'NO',
                '6702.90.00': 'NO',
                '9401.80.00': 'NO',
                '8715.00.00': 'NO',
                '8715.00.00': 'NO',
                '3005.90.00': 'KG',
                '4911.10.00': 'KG',
                '3922.10.00': 'M2',
                '8506.50.00': 'NO',
                '3304.99.00': 'KG',
                '9801.00.33': 'NO',
                '1521.90.00': 'KG',
                '4203.30.00': 'NO',
                '8712.00.00': 'NO',
                '8714.99.00': 'KG',
                '4011.50.00': 'NO',
                '9005.80.00': 'NO',
                '8407.21.00': 'NO',
                '7616.10.00': 'KG',
                '9801.00.54': 'KG',
                '4901.10.00': 'KG',
                '4819.20.00': 'KG',
                '9603.10.00': 'NO',
                '8429.52.00': 'NO',
                '9403.40.00': 'NO',
                '8470.10.00': 'NO',
                '4910.00.00': 'KG',
                '9801.00.22': 'NO',
                '8525.80.00': 'NO',
                '6306.90.00': 'KG',
                '5908.00.00': 'KG',
                '5907.00.00': 'M2',
                '8507.60.00': 'NO',
                '8708.29.00': 'NO',
                '3819.00.00': 'KG',
                '9802.00.79': 'NO',
                '8527.29.00': 'NO',
                '9801.00.37': 'NO',
                '9401.80.00': 'NO',
                '8511.10.10': 'HUN',
                '9801.00.49': 'KG',
                '2523.21.00': 'TON',
                '9802.00.85': 'NO',
                '1806.90.00': 'KG',
                '9505.10.00': 'NO',
                '2402.20.00': 'THS',
                '2402.10.00': 'THS',
                '6307.10.00': 'KG',
                '3402.20.00': 'KG',
                '9103.90.00': 'NO',
                '9802.00.62': 'KG',
                '0901.11.00': 'KG',
                '8516.71.00': 'NO',
                '7118.10.20': 'G',
                '9802.00.71': 'NO',
                '9802.00.51': 'KG',
                '9802.00.55': 'KG',
                '9001.30.00': 'PR',
                '3925.10.00': 'X',
                '8443.99.00': 'KG',
                '9801.00.49': 'KG',
                '6303.12.00': 'NO',
                '7323.93.00': 'KG',
                '9802.00.52': 'KG',
                '3307.20.00': 'KG',
                '3402.20.00': 'KG',
                '9619.00.00': 'NO',
                '9801.00.27': 'KG',
                '9801.00.39': 'NO',
                '3808.94.00': 'KG',
                '9618.00.00': 'NO',
                '9801.00.10': 'KG',
                '2309.10.00': 'KG',
                '2309.90.20': 'KG',
                '7610.10.00': 'NO',
                '8711.90.20': 'NO',
                '9802.00.78': 'NO',
                '9506.91.00': 'NO',
                '5208.11.00': 'KG',
                '8414.59.00': 'NO',
                '3101.00.00': 'KG',
                '3701.20.00': 'M2',
                '3006.50.00': 'KG',
                '9507.20.00': 'NO',
                '6307.90.20': 'KG',
                '6307.90.10': 'KG',
                '9006.69.00': 'NO',
                '3918.10.00': 'M2',
                '2106.90.00': 'KG',
                '9403.89.00': 'NO',
                '3005.90.00': 'KG',
                '9004.90.00': 'DOZ',
                '7013.28.00': 'NO',
                '6216.00.00': 'NO',
                '3506.99.00': 'KG',
                '9004.90.00': 'DOZ',
                '9506.32.00': 'NO',
                '9506.39.00': 'NO',
                '9802.00.65': 'NO',
                '4202.31.00': 'NO',
                '4421.10.00': 'NO',
                '6505.00.00': 'KG',
                '8518.30.00': 'NO',
                '6301.20.00': 'NO',
                '0409.00.00': 'KG',
                '4009.12.00': 'KG',
                '4016.95.00': 'NO',
                '3215.11.00': 'KG',
                '3808.61.00': 'KG',
                '2937.12.00': 'KG',
                '6304.99.00': 'KG',
                '8516.79.00': 'NO',
                '9802.00.66': 'NO',
                '7108.12.00': 'G',
                '7117.19.00': 'NO',
                '9802.00.67': 'NO',
                '8301.70.00': 'KG',
                '3924.10.00': 'KG',
                '4821.10.00': 'KG',
                '9405.40.00': 'NO',
                '8433.11.00': 'NO',
                '4202.31.00': 'NO',
                '4203.40.00': 'NO',
                '6307.20.00': 'KG',
                '9613.20.00': 'NO',
                '8302.41.00': 'KG',
                '8301.40.00': 'DOZ',
                '3006.70.00': 'KG',
                '4202.12.00': 'NO',
                '8214.20.00': 'NO',
                '4905.99.00': 'KG',
                '9020.00.00': 'NO',
                '9019.10.00': 'NO',
                '9404.29.00': 'NO',
                '8518.10.00': 'NO',
                '9011.10.00': 'NO',
                '0402.21.00': 'KG',
                '7009.92.00': 'NO',
                '9801.00.61': 'KG',
                '5608.90.10': 'KG',
                '8714.10.00': 'KG',
                '8433.20.00': 'NO',
                '9209.99.00': 'NO',
                '9206.00.00': 'NO',
                '9201.10.00': 'NO',
                '9202.90.00': 'NO',
                '9205.90.00': 'NO',
                '8310.00.00': 'KG',
                '9801.00.38': 'NO',
                '8304.00.00': 'KG',
                '4819.60.00': 'KG',
                '9801.00.53': 'KG',
                '3811.90.00': 'KG',
                '2804.40.11': 'M3',
                '8301.40.00': 'KG',
                '3208.10.00': 'L',
                '4810.13.00': 'KG',
                '4803.00.00': 'KG',
                '1211.90.00': 'KG',
                '9401.90.00': 'NO',
                '8716.90.00': 'NO',
                '9505.90.00': 'NO',
                '7016.90.00': 'NO',
                '2008.19.00': 'KG',
                '9608.10.00': 'NO',
                '3303.00.10': 'KG',
                '9801.00.20': 'NO',
                '4414.00.00': 'NO',
                '4911.91.00': 'KG',
                '9614.00.00': 'NO',
                '8432.31.00': 'NO',
                '9701.90.00': 'NO',
                '9802.00.88': 'NO',
                '4817.20.00': 'KG',
                '8443.39.00': 'NO',
                '9008.50.00': 'NO',
                '8526.92.00': 'NO',
                '8527.13.00': 'NO',
                '8212.20.00': 'NO',
                '8418.21.00': 'NO',
                '7312.10.00': 'KG',
                '5702.10.00': 'KG',
                '8303.00.00': 'KG',
                '6506.10.00': 'KG',
                '2501.00.00': 'KGS',
                '8423.10.00': 'NO',
                '3926.10.00': 'KG',
                '8213.00.00': 'NO',
                '1209.99.00': 'KG',
                '8452.10.00': 'NO',
                '3305.10.00': 'KG',
                '6404.19.00': 'PR',
                '8310.00.00': 'KG',
                '3401.11.00': 'KG',
                '9802.00.54': 'KG',
                '8541.40.10': 'NO',
                '8518.21.00': 'NO',
                '9506.99.00': 'NO',
                '4820.90.00': 'KG',
                '8306.21.00': 'KG',
                '4811.41.00': 'KG',
                '8418.50.00': 'NO',
                '7321.11.00': 'KG',
                '8715.00.00': 'NO',
                '1704.90.00': 'KG',
                '9307.00.00': 'NO',
                '5906.10.00': 'KG',
                '0902.10.00': 'KG',
                '9005.80.00': 'NO',
                '9802.00.76': 'NO',
                '9506.51.00': 'NO',
                '9025.11.00': 'NO',
                '6904.90.00': 'thousands',
                '4011.10.00': 'NO',
                '4803.00.00': 'KG',
                '9802.00.53': 'KG',
                '3303.00.20': 'KG',
                '8205.51.00': 'NO',
                '9802.00.69': 'NO',
                '9802.00.70': 'NO',
                '9801.00.52': 'NO',
                '9620.00.00': 'NO',
                '7115.90.00': 'NO',
                '8519.30.00': 'NO',
                '8528.72.00': 'NO',
                '6603.90.00': 'DOZ',
                '6601.10.00': 'DOZ',
                '8508.60.00': 'NO',
                '9802.00.77': 'NO',
                '2936.29.00': 'KG',
                '4202.31.00': 'NO',
                '4202.32.00': 'NO',
                '4814.20.00': 'KG',
                '9113.90.00': 'KG',
                '9801.00.19': 'NO',
                '8516.10.00': 'NO',
                '8713.90.00': 'NO',
                '9802.00.61': 'KG',
                '2204.21.00': 'LTR',
                '5606.00.00': 'KG',
                '4813.20.00': 'KG',
            }


            # Example usage:
                qty_unit = product_units.get(traffic_code_val, 'KG')
                # Assuming weight_lbs_val is a floating-point variable, round it to fewer decimal places
                weight_lbs_val = round(weight_lbs_val, 2)  # Adjust the number of decimal places as needed

                # Get the UOM from the product_units dictionary based on traffic code
                 # 'N/A' is the default value if traffic code is not found in the dictionary

                # Calculate net_freight for each row
                freight_price = (netfreight_float / float(grosswt)) * float(weight_lbs_val)

                # Calculate insurance price for each value and its corresponding net freight
                insurance_price = (float(values_str_list_val) + freight_price) * 0.01

                # Create CSVData entry
                csv_data = CSVData(
                    manifest_id=manifest.id,
                    consignee=consignee_val,
                    description_code=description_code_val,
                    tin_number=tin_number_val,
                    values_str_list=values_str_list_val,
                    traffic_code=traffic_code_val,
                    mawb=mawb_val,
                    weight_lbs=weight_lbs_val,
                    insurance_price=insurance_price,
                    freight_price=freight_price,
                    quantity=piece_val,
                    qty_unit = qty_unit   # Use qty_unit_val directly here
                )

                # Associate CSVData with net_freight
                csv_data.net_freight = freight_price

                # Associate CSVData with insurance_price
                csv_data.insurance_price = insurance_price

                db.session.add(csv_data)

            # Commit the CSVData entries
            db.session.commit()
            return redirect(url_for('index'))
     # Render the edit_manifest.html template with the manifest data for editing
    return render_template('aeropost_form.html')


@app.route('/edit_manifest/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_manifest(id):
    # Fetch the manifest with the given ID from the database
    manifest = Manifest.query.get_or_404(id)
    csv_data = CSVData.query.filter_by(manifest_id=id).all()


    if request.method == 'POST':
        # Update the manifest data based on the form submission
        manifest.dateOfEntry = request.form.get('doe')
        manifest.airLine = request.form.get('vesselcode')
        manifest.flightNumber = request.form.get('voyogeno')
        manifest.carrier = request.form.get('carrier')
        manifest.carriername = request.form.get('carriername')
        manifest.shippingport = request.form.get('shippingport')
        manifest.billnumber = request.form.get('billnumber')
        manifest.pkgcount = request.form.get('pkgcount')
        manifest.pkgtype = request.form.get('pkgtype')
        manifest.grosswt = request.form.get('grosswt')
        manifest.grosswtunit = request.form.get('grosswtunit')
        manifest.grossvol = request.form.get('grossvol')
        manifest.grossvolunit = request.form.get('grossvolunit')
        manifest.ffname = request.form.get('ffname')
        manifest.ffaddress = request.form.get('ffaddress')
        manifest.ffcity = request.form.get('ffcity')
        manifest.ffstate = request.form.get('ffstate')
        manifest.ffcountry = request.form.get('ffcountry')
        manifest.ffzip = request.form.get('ffzip')
        manifest.netcost = request.form.get('netcost')
        manifest.netfreight = request.form.get('netfreight')
        manifest.arrivaldate = request.form.get('arrivaldate')
        manifest.departuredate = request.form.get('departuredate')
        manifest.dischargeport = request.form.get('dischargeport')
        manifest.tod = request.form.get('tod')
        manifest.categoryofgoods = request.form.get('categoryofgoods')
        manifest.regime = request.form.get('regime')
        manifest.contents = request.form.get('contents')

        # Save the changes to the database
        db.session.commit()

        # Redirect to a page showing the updated manifest or any other appropriate route
        flash('Manifest updated successfully', 'success')
        return redirect(url_for('index'))

    # Render the edit_manifest.html template with the manifest data for editing
    return render_template('edit_manifest.html', manifest=manifest, csv_data=csv_data)


@app.route('/edit_csv/<int:manifest_id>/<int:csv_id>', methods=['GET', 'POST'])
@login_required
def edit_csv(manifest_id, csv_id):
    # Fetch the CSV entry from the database
    csv_entry = CSVData.query.get_or_404(csv_id)

    # Check if the CSV entry belongs to the specified manifest
    if csv_entry.manifest_id != manifest_id:
        flash('Invalid request', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Update the CSV entry data based on the form submission
        csv_entry.consignee = request.form.get('consignee')
        csv_entry.description_code = request.form.get('description_code')
        csv_entry.tin_number = request.form.get('tin_number')
        csv_entry.values_str_list = request.form.get('values_str_list')
        csv_entry.traffic_code = request.form.get('traffic_code')
        csv_entry.mawb = request.form.get('mawb')
        csv_entry.weight_lbs = request.form.get('weight_lbs')
        csv_entry.freight_price = request.form.get('freight_price')
        csv_entry.insurance_price = request.form.get('insurance_price')
        csv_entry.quantity = request.form.get('quantity')
        csv_entry.qty_unit = request.form.get('qty_unit')

        # Save the changes to the database
        db.session.commit()

        # Redirect to the edit_manifest route or any other appropriate route
        flash('CSV entry updated successfully', 'success')
        return redirect(url_for('edit_manifest', id=manifest_id))

    # Render the edit_csv.html template with the CSV entry data for editing
    return render_template('edit_csv.html', manifest_id=manifest_id, csv_entry=csv_entry)


@app.route('/delete_manifest/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_manifest(id):
    # Assuming your model is called Manifest
    manifest = Manifest.query.get_or_404(id)

    if request.method == 'POST':
        try:
            db.session.delete(manifest)
            db.session.commit()
            flash('Manifest deleted successfully', 'success')
            return redirect(url_for('index'))  # Redirect to the main route after deletion
        except Exception as e:
            flash(f'Deletion failed. {e}', 'danger')

    return render_template('manifests.html', manifest=manifest)


@app.route('/delete_csv/<int:manifest_id>/<int:csv_id>', methods=['POST'])
@login_required
def delete_csv(manifest_id, csv_id):
    # Fetch the CSV entry from the database
    csv_entry = CSVData.query.get_or_404(csv_id)

    # Check if the CSV entry belongs to the specified manifest
    if csv_entry.manifest_id != manifest_id:
        flash('Invalid request', 'error')
        return redirect(url_for('index'))

    # Delete the CSV entry from the database
    db.session.delete(csv_entry)
    db.session.commit()

    flash('CSV entry deleted successfully', 'success')
    return redirect(url_for('edit_manifest', id=manifest_id))


@app.route('/search_manifests', methods=['GET', 'POST'])
def search_manifests():
    if request.method == 'GET':
        # Get the bill number from the query string
        bill_number = request.args.get('bill_number', '')

        # Perform the search based on the entered bill number
        # Assuming your model is called Manifest
        manifests = Manifest.query.filter(Manifest.billnumber.ilike(f'%{bill_number}%')).all()

        return render_template('manifests.html', items=manifests)

    return redirect(url_for('index'))  # Replace 'your_main_route' with the actual route


@app.route('/download_manifest/<int:id>', methods=['GET', 'POST'])
@login_required
def download_manifest(id):
    manifest = Manifest.query.get_or_404(id)

    
    # Sum up the freight_price from CSVData
    total_freight_price = db.session.query(func.sum(CSVData.freight_price)).filter_by(manifest_id=id).scalar()
    total_insurance_price = db.session.query(func.sum(CSVData.insurance_price)).filter_by(manifest_id=id).scalar()

    # Get all distinct Tin Numbers for the given manifest
    tin_numbers = db.session.query(CSVData.tin_number).filter_by(manifest_id=id).distinct().all()
    tin_numbers = [tin[0] for tin in tin_numbers]
    
    # Generate XML
    root = Element("SADEntry")
    # Get the current date
    current_date = dt.now().date()
    formatted_date = current_date.strftime("%Y-%m-%d")

    # Add the current date to the "Date" XML element
    SubElement(root, "Date").text = formatted_date


    SubElement(root, "Regime").text = manifest.regime 

    importer = SubElement(root, 'Importer')
    SubElement(importer, 'Number').text = '20001428'

    exporter = SubElement(root, 'Exporter')
    SubElement(exporter, 'Name').text = manifest.ffname
    SubElement(exporter, 'Address').text = manifest.ffaddress
    SubElement(exporter, 'City').text = manifest.ffcity
    SubElement(exporter, 'State').text = manifest.ffstate
    SubElement(exporter, 'PostalCode').text = manifest.ffzip
    SubElement(exporter, 'Country').text = manifest.ffcountry

    consignment = SubElement(root, 'Consignment')
    SubElement(consignment, 'DepartureDate').text = manifest.departuredate
    SubElement(consignment, 'ArrivalDate').text = manifest.arrivaldate
    SubElement(consignment, 'ExportCountry').text = 'USA'
    SubElement(consignment, 'ImportCountry').text = 'CYM'
    SubElement(consignment, 'ShippingPort').text = manifest.shippingport
    SubElement(consignment, 'DischargePort').text = manifest.dischargeport
    SubElement(consignment, 'TransportMode').text = manifest.transportation 

    shipment = SubElement(root, 'Shipment')
    SubElement(shipment, 'VesselCode').text = manifest.airLine
    SubElement(shipment, 'VoyageNo').text = manifest.flightNumber
    SubElement(shipment, 'ShippingAgent').text = manifest.airLine
    SubElement(shipment, 'BillNumber').text = manifest.billnumber
    SubElement(shipment, 'BillType').text = 'CONSOLIDATED'

    packages = SubElement(root, 'Packages')
    SubElement(packages, 'PkgCount').text = manifest.pkgcount
    SubElement(packages, 'PkgType').text = manifest.pkgtype
    SubElement(packages, 'GrossWt').text = manifest.grosswt
    SubElement(packages, 'GrossWtUnit').text = manifest.grosswtunit
    SubElement(packages, 'GrossVol').text = manifest.grossvol
    SubElement(packages, 'GrossVolUnit').text = manifest.grossvolunit
    SubElement(packages, 'Contents').text = manifest.contents
    SubElement(packages, 'CategoryOfGoods').text = manifest.categoryofgoods


    valuation = SubElement(root, 'Valuation')
    SubElement(valuation, 'Currency').text = 'USD'
    SubElement(valuation, 'NetCost').text = manifest.netcost
    SubElement(valuation, 'NetInsurance').text = str(total_insurance_price)
    SubElement(valuation, 'NetFreight').text = str(total_freight_price) 
    
    SubElement(valuation, 'TermsOfDelivery').text = 'FOB'

    SubElement(root, 'MoneyDeclaredFlag').text = 'N'

    consolidated_shipment = SubElement(root, 'ConsolidatedShipment')

    prefix_counter = 1

    for tin in tin_numbers:
        consolidated_item = SubElement(consolidated_shipment, 'ConsolidatedItem')

        importer_consolidated = SubElement(consolidated_item, 'Importer')
        SubElement(importer_consolidated, 'Number').text = tin

        exporter_consolidated = SubElement(consolidated_item, 'Exporter')
        SubElement(exporter_consolidated, 'Name').text = manifest.ffname
        SubElement(exporter_consolidated, 'Address').text = manifest.ffaddress
        SubElement(exporter_consolidated, 'City').text = manifest.ffcity
        SubElement(exporter_consolidated, 'State').text = manifest.ffstate
        SubElement(exporter_consolidated, 'PostalCode').text = manifest.ffzip
        SubElement(exporter_consolidated, 'Country').text = manifest.ffcountry
        SubElement(exporter_consolidated, 'Phone')

        finance_consolidated = SubElement(consolidated_item, 'Finance')
        SubElement(finance_consolidated, 'FinanceParty').text = 'T'
        SubElement(finance_consolidated, 'GuaranteeType').text = 'BD'

        # Increment the prefix counter by 100 for the next iteration
        prefix_counter += 100

        # Get the first 5 characters of the user's name from the 'consignee' column in CSVData table
        user_name_prefix = db.session.query(CSVData.consignee).filter_by(manifest_id=id, tin_number=tin).first()
        user_name_prefix = user_name_prefix[0][:5] if user_name_prefix else ""

        # Get the last 4 digits of the 'mawb' column in CSVData table
        mawb_last_four_digits = db.session.query(CSVData.mawb).filter_by(manifest_id=id, tin_number=tin).first()
        mawb_last_four_digits = mawb_last_four_digits[0][-4:] if mawb_last_four_digits else ""

        # Construct the final result with the incremented "101PM" portion
        final_result = f"{user_name_prefix}-{prefix_counter}PM-{mawb_last_four_digits}"
        


        SubElement(consolidated_item, 'BillNumber').text = final_result

        # Get additional data for Packages
        pkg_count = db.session.query(func.sum(CSVData.quantity)).filter_by(manifest_id=id, tin_number=tin).scalar()
        pkg_type = db.session.query(Manifest.pkgtype).filter_by(id=id).scalar()
        gross_wt_unit = db.session.query(Manifest.grosswtunit).filter_by(id=id).scalar()
        carrier = db.session.query(Manifest.carrier).filter_by(id=id).scalar()
        # Assuming the results are tuples, you can use [0] to get the first element of each tuple
        mawb_result = db.session.query(CSVData.mawb).filter_by(manifest_id=id, tin_number=tin).first()[0]
        consignee_result = db.session.query(CSVData.consignee).filter_by(manifest_id=id, tin_number=tin).first()[0]
        contents_result = db.session.query(Manifest.contents).filter_by(id=id).scalar()

        # Format the results as needed
        contents = f"{mawb_result} - {consignee_result} - {contents_result}"
        category_of_goods = db.session.query(Manifest.categoryofgoods).filter_by(id=id).scalar()



        # Create the 'Packages' element and add sub-elements
        packages = SubElement(consolidated_item, 'Packages')
        SubElement(packages, 'PkgCount').text = str(pkg_count)
        SubElement(packages, 'PkgType').text = pkg_type
        SubElement(packages, 'GrossWt').text = '0.00'
        SubElement(packages, 'GrossWtUnit').text = gross_wt_unit
        SubElement(packages, 'GrossVol').text = '0'
        SubElement(packages, 'GrossVolUnit').text = manifest.grossvolunit
        SubElement(packages, 'Contents').text = contents
        SubElement(packages, 'CategoryOfGoods').text = str(category_of_goods)

         
        netcost = db.session.query(func.sum(CSVData.values_str_list)).filter_by(manifest_id=id, tin_number=tin).scalar()
        netinsurance = db.session.query(func.sum(CSVData.insurance_price)).filter_by(manifest_id=id, tin_number=tin).scalar()
        netfreight = db.session.query(func.sum(CSVData.freight_price)).filter_by(manifest_id=id, tin_number=tin).scalar()

        valuation = SubElement(consolidated_item, 'Valuation')
        SubElement(valuation, 'Currency').text = 'USD'
        SubElement(valuation, 'NetCost').text = str(netcost)
        SubElement(valuation, 'NetInsurance').text = str(netinsurance)
        SubElement(valuation, 'NetFreight').text = str(netfreight)
        SubElement(valuation, 'TermsOfDelivery').text = str(manifest.tod)

        # Get data for each Tin Number
        tin_data = CSVData.query.filter_by(manifest_id=id, tin_number=tin).all()
        for item in tin_data:
            item_element = SubElement(consolidated_item, 'Items')

            SubElement(item_element, 'Code').text = item.traffic_code
            SubElement(item_element, 'Desc').text = item.description_code
            SubElement(item_element, 'CPC').text = 'IM100'
            SubElement(item_element, 'Preference').text = '0'
            SubElement(item_element, 'Origin').text = 'USA'
            SubElement(item_element, 'Qty').text = str(item.quantity)
            SubElement(item_element, 'QtyUnit').text = 'KG'
            SubElement(item_element, 'Cost').text = item.values_str_list
            SubElement(item_element, 'Insurance').text = str(item.insurance_price)
            SubElement(item_element, 'Freight').text = str(item.freight_price)
            SubElement(item_element, 'InvNumber').text = 'ATTACHED'
            SubElement(item_element, 'WaiverPct').text = '0.00'

        SubElement(consolidated_item, 'MoneyDeclaredFlag').text = 'N'
       

    xml_str = minidom.parseString(tostring(root, encoding='utf-8')).toprettyxml(indent="    ")

# Save the XML content to a variable
    xml_str = minidom.parseString(tostring(root, encoding='utf-8')).toprettyxml(indent="    ")

    # Return the XML content as a downloadable attachment
    return send_file(
        io.BytesIO(xml_str.encode('utf-8')),
        mimetype='application/xml',
        as_attachment=True,
        download_name=f"manifest_{manifest.id}_data23.xml"
    )
    flash(f'XML file generated successfully: {file_path}', 'success')
    # return redirect(url_for('display_data_by_tin', id=id))


if __name__ == '__main__':
    app.run(debug=True)

  # ET.SubElement(valuation, 'NetInsurance').text = str(manifest.insurance_prices)
        # ET.SubElement(valuation, 'NetFreight').text = manifest.netfreight