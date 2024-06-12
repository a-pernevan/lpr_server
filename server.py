import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
import mysql.connector
from dotenv import load_dotenv
import os

class MyRequestHandler(BaseHTTPRequestHandler):
    load_dotenv()
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            print("Received JSON data:")
            print(json.dumps(json_data, indent=4))  # Print the entire JSON
            
            if json_data.get('Active') == "keepAlive":
                print("Ping")

            else:
                plate_number = json_data.get('Picture', {}).get('Plate').get('PlateNumber')
                camera = json_data.get('Picture', {}).get('SnapInfo').get('DeviceID')
                date_time = str(json_data.get('Picture', {}).get('SnapInfo').get('AccurateTime')).split('.')[0]
                print(date_time)
                if camera == "e6f9fe93-8e4d-8f79-65f0-58cd4b6a8e4d":
                    direction = "in"
                    if plate_number:
                        print("Plate Number: " + plate_number + " Direction: " + direction)
                        self.save_plate(plate_number)
                        # print(f"Extracted Plate Number: {plate_number}")
                    else:
                        print("No Plate Number found in the received JSON.")
                    
            #plate_pic = json_data.get("Picture", {}).get("CutoutPic").get("Content")
            #print(plate_pic)
                # if plate_number:
                #     print(f"Extracted Plate Number: {plate_number}")
                #     # self.save_plate(plate_number)
                # else:
                #     print("No Plate Number found in the received JSON.")
        except json.JSONDecodeError:
            print("Error decoding JSON data.")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response_data = {"Result": True}
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        

    def save_plate(self, plate_number):
        now = datetime.datetime.now()
        now_format = now.strftime("%Y-%m-%d")

        try:
            self.tms_db = mysql.connector.connect(
                host = os.getenv("HOST"),
                user = os.getenv("USER"),
                passwd = os.getenv("PASS"),
                database = os.getenv("DB"),
                auth_plugin='mysql_native_password'
            )
        except:
            print("Could not connect to MySQL")
            quit()
        # Generam un nou cursor
        self.my_cursor = self.tms_db.cursor()
        add_plate = ("INSERT INTO lpr_cam (plate_no, status, date_in) VALUES (%s, %s, %s)")
        values = (plate_number, "CHECK", now_format)

        self.my_cursor.execute(add_plate, values)
        self.tms_db.commit()
        self.my_cursor.close()
        self.tms_db.close()
        self.check_plate(plate_number)
    
    def check_plate(self, plate_number):
        try:
            self.tms_db = mysql.connector.connect(
                host = os.getenv("HOST"),
                user = os.getenv("USER"),
                passwd = os.getenv("PASS"),
                database = os.getenv("DB"),
                auth_plugin='mysql_native_password'
            )
        except:
            print("Could not connect to MySQL")
            quit()
        # Generam un nou cursor
        self.my_cursor = self.tms_db.cursor()
        self.my_cursor.execute("SELECT plate_no FROM tauros_truck WHERE plate_no = %s", (plate_number,))
        result = self.my_cursor.fetchone()

        if result:
            # Camionul este Tauros
            self.my_cursor.execute("UPDATE lpr_cam SET status = 'PARKED' WHERE plate_no = %s AND status = 'CHECK'", (plate_number,))
            self.my_cursor.execute("UPDATE lpr_cam SET label = 'Tauros' WHERE plate_no = %s AND status = 'PARKED'", (plate_number,))
            self.tms_db.commit()
        else:
            # Camionul nu este Tauros / TO-DO : Implementare functie de verificare
            self.my_cursor.execute("UPDATE lpr_cam SET status = 'PARKED' WHERE plate_no = %s AND status = 'CHECK'", (plate_number,))
            self.my_cursor.execute("UPDATE lpr_cam SET label = 'Other' WHERE plate_no = %s AND status = 'PARKED'", (plate_number,))
            self.tms_db.commit()
        
        self.my_cursor.close()
        self.tms_db.close()
        




def run_server():
    server_address = ('', 7080)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print("Server started on port 7080...")
    httpd.serve_forever()


if __name__ == '__main__':
	run_server()
