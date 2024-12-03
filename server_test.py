import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
import os
import mysql.connector
import requests
import threading
import time
from datetime import datetime
from parking_mail import Parking_notification, Tauros_truck_park

class MyRequestHandler(BaseHTTPRequestHandler):
    load_dotenv()
    ESP8266_IP = 'http://192.168.200.158'

    def turn_led_on(self):
        response = requests.get(f'{self.ESP8266_IP}/?led=on')
        # if response.status_code == 200:
        #     print('LED turned ON')
        # else:
        #     print('Failed to turn LED ON')

    def turn_led_off(self):
        response = requests.get(f'{self.ESP8266_IP}/?led=off')
        time.sleep(10)
        response = requests.get(f'{self.ESP8266_IP}/?led=on')
        # if response.status_code == 200:
        #     print('LED turned OFF')
        # else:
        #     print('Failed to turn LED OFF')

    def blink_led(self):
        response = requests.get(f'{self.ESP8266_IP}/?led=blink')

        # if response.status_code == 200:
        #     print('LED blinks')
        # else:
        #     print('Failed to blink LED')

    def run_blink_led_thread(self):
        thread = threading.Thread(target=self.blink_led)
        thread.start()

    def run_turn_led_off_thread(self):
        thread = threading.Thread(target=self.turn_led_off)
        thread.start()

    lpr_2 = "f5ea9239-9869-9e13-376a-e9d24ab89869"
    lpr_1 = "e6f9fe93-8e4d-8f79-65f0-58cd4b6a8e4d"

    def do_POST(self):
        # try:
        #     self.turn_led_on()
        
        # except:
        #     print("Error turning LED on")
            
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            # print("Received JSON data:")
            # print(json.dumps(json_data, indent=4))  # Print the entire JSON

            if json_data.get('Active') == "keepAlive":
                if str(json_data.get('DeviceID')) == self.lpr_1:
                    print("Ping LPR 1")
                
                if str(json_data.get('DeviceID')) == self.lpr_2:
                    print("Ping LPR 2")

            else:
                if json_data.get('Picture', {}).get('SnapInfo').get('DeviceID') == self.lpr_1:       
                    plate_number = json_data.get('Picture', {}).get('Plate').get('PlateNumber')
                    date_time = json_data.get('Picture', {}).get('SnapInfo').get('AccurateTime')
                    cam_date_time = date_time.split('.')[0]
                    cam_date = str(cam_date_time.split(" ")[0])
                    cam_time = cam_date_time.split(" ")[1]
                    token = json_data.get('Picture', {}).get('SnapInfo').get('DefenceCode')
                    # print(date_time.split('.')[0])
                    if str(json_data.get('Picture', {}).get('SnapInfo').get('Direction')) == "Obverse":
                        # print("IN! - LPR1")
                        self.truck(plate_number, "IN", cam_date, cam_time, token)
                        
                    # elif str(json_data.get('Picture', {}).get('SnapInfo').get('Direction')) == "Reverse":
                    #     print("OUT - LPR1")
            #plate_pic = json_data.get("Picture", {}).get("CutoutPic").get("Content")
            #print(plate_pic)
                    if plate_number:
                        print(f"Extracted Plate Number: {plate_number}")
                    else:
                        print("No Plate Number found in the received JSON.")

                if json_data.get('Picture', {}).get('SnapInfo').get('DeviceID') == self.lpr_2:
                        plate_number = json_data.get('Picture', {}).get('Plate').get('PlateNumber')
                        date_time = json_data.get('Picture', {}).get('SnapInfo').get('AccurateTime')
                        cam_date_time = date_time.split('.')[0]
                        cam_date = str(cam_date_time.split(" ")[0])
                        cam_time = cam_date_time.split(" ")[1]
                        token = json_data.get('Picture', {}).get('SnapInfo').get('DefenceCode')
                        # print(date_time.split('.')[0])
                        if str(json_data.get('Picture', {}).get('SnapInfo').get('Direction')) == "Obverse":
                            # print("OUT - LPR2")
                            self.truck(plate_number, "OUT", cam_date, cam_time, token)
                        # elif str(json_data.get('Picture', {}).get('SnapInfo').get('Direction')) == "Reverse":
                        #     print("IN - LPR2")
                #plate_pic = json_data.get("Picture", {}).get("CutoutPic").get("Content")
                #print(plate_pic)
                        if plate_number:
                            print(f"Extracted Plate Number: {plate_number}")
                        else:
                            print("No Plate Number found in the received JSON.")
        except json.JSONDecodeError:
            print("Error decoding JSON data.")

        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response_data = {"Result": True}
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def log_message(self, format, *args):
        return  # Suppress log output
    
    def truck(self, plate_number, direction, cam_date, cam_time, token):
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

        self.my_cursor = self.tms_db.cursor()
        # Check if Tauros Truck
        self.my_cursor.execute("SELECT plate_no, categorie from tauros_truck WHERE plate_no = %s", (plate_number,))
        self.result = self.my_cursor.fetchall()
        self.my_cursor.execute("SELECT place_id, plate_no from tauros_park_main where plate_no = %s AND place_status <> 'PLECAT'", (plate_number,))
        self.result_samsung = self.my_cursor.fetchall()
        

        if self.result:
            label = "Tauros"
            if direction == "IN":
                truck_directie = "Intrare"
                token = "OK"
            elif direction == "OUT":
                truck_directie = "Iesire"
                token = "OK"
            add_truck = ("INSERT IGNORE INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
            values = (plate_number, cam_date, cam_time, direction, label, token)
            self.my_cursor.execute(add_truck, values)
            self.tms_db.commit()
            self.my_cursor.execute("SELECT id FROM registru ORDER BY id DESC LIMIT 1")
            self.last_id = self.my_cursor.fetchone()

            data_in_out = str(cam_date) + " " + str(cam_time)
            sql = ("INSERT IGNORE INTO tauros_truck_park (lpr_id, truck, directie, data_in_out) VALUES (%s, %s, %s, %s)")
            values = (self.last_id[0], plate_number, truck_directie, data_in_out)
            self.my_cursor.execute(sql, values)
            self.tms_db.commit()
            self.my_cursor.close()
            self.tms_db.close()
            tauros_mail_notify = Tauros_truck_park(self.last_id[0], direction)
            # if direction == "IN":
            #     try:
            #         self.run_turn_led_off_thread()
            #     except:
            #         pass
        elif self.result_samsung:
            label = "Samsung"
            if direction == "IN":
                truck_directie = "PARCAT"
                token = "OK"
                date_in_real = str(cam_date) + " " + str(cam_time)
                add_truck = ("INSERT IGNORE INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
                values = (plate_number, cam_date, cam_time, direction, label, token)
                self.my_cursor.execute(add_truck, values)
                self.tms_db.commit()
                self.my_cursor.execute("SELECT id FROM registru ORDER BY id DESC LIMIT 1")
                self.last_id = self.my_cursor.fetchone()
                samsung_id = self.result_samsung[0][0]
                # print(samsung_id)
                sql = ("UPDATE tauros_park_main SET place_status=%s, date_in_real=%s, lpr_id=%s WHERE place_id=%s")
                values = (truck_directie, date_in_real, self.last_id[0], samsung_id)
                self.my_cursor.execute(sql, values)
                self.tms_db.commit()
                self.my_cursor.close()
                self.tms_db.close()
                mail_msg = Parking_notification(samsung_id, direction)

            elif direction == "OUT":
                truck_directie = "PLECAT"
                token = "OK"
                date_out_real = str(cam_date) + " " + str(cam_time)
                samsung_id = self.result_samsung[0][0]
                self.my_cursor.execute("SELECT id FROM registru ORDER BY id DESC LIMIT 1")
                self.last_id = self.my_cursor.fetchone()
                sql = ("UPDATE tauros_park_main SET place_status=%s, date_in_out=%s, lpr_id=%s WHERE place_id=%s")
                values = (truck_directie, date_out_real, self.last_id[0], samsung_id)
                self.my_cursor.execute(sql, values)
                self.tms_db.commit()
                date_in_out = "SELECT date_in_real, date_in_out FROM tauros_park_main WHERE place_id = %s"
                self.my_cursor.execute(date_in_out, (samsung_id,))
                date_in_real = self.my_cursor.fetchone()
                parking_time_sec = (date_in_real[1] - date_in_real[0]).total_seconds() / 3600
                parking_time = round(parking_time_sec, 0)
                sql = ("UPDATE tauros_park_main SET park_real=%s WHERE place_id=%s")
                values = (parking_time, samsung_id)
                self.my_cursor.execute(sql, values)
                self.tms_db.commit()
                self.my_cursor.close()
                self.tms_db.close()
                mail_msg = Parking_notification(samsung_id, direction)
        else:
            label = "Other"
            # add_truck = ("INSERT INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
            # values = (plate_number, cam_date, cam_time, direction, label, "CHECK")
            # self.my_cursor.execute(add_truck, values)
            # self.tms_db.commit()
            if direction == "IN":
                truck_directie = "PARCAT"
                token = "OK"
                add_truck = ("INSERT IGNORE INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
                values = (plate_number, cam_date, cam_time, direction, label, token)
                self.my_cursor.execute(add_truck, values)
                self.tms_db.commit()
                self.my_cursor.execute("SELECT id FROM registru ORDER BY id DESC LIMIT 1")
                self.last_id = self.my_cursor.fetchone()
                sql = ("INSERT IGNORE INTO reg_visit (nr_auto, data_in, ora_in, visit_status, create_date, lpr_id) VALUES (%s, %s, %s, %s, %s, %s)")
                values = (plate_number, cam_date, cam_time, "PARCAT", datetime.now(), self.last_id[0])
                self.my_cursor.execute(sql, values)
                self.tms_db.commit()

            elif direction == "OUT":
                truck_directie = "IESIT"
                token = "OK"
                sql = ("SELECT id FROM registru WHERE cap_tractor = %s ORDER BY id DESC LIMIT 1")
                values = (plate_number,)
                self.my_cursor.execute(sql, values)
                self.last_id = self.my_cursor.fetchone()
                if self.last_id:
                    sql = ("UPDATE registru SET token = %s WHERE id = %s")
                    values = (token, self.last_id[0])
                    self.my_cursor.execute(sql, values)
                    self.tms_db.commit()
                    sql = ("UPDATE reg_visit SET data_out = %s, ora_out = %s, visit_status = %s WHERE lpr_id = %s")
                    values = (cam_date, cam_time, "IESIT", self.last_id[0])
                    self.my_cursor.execute(sql, values)
                    self.tms_db.commit()
                else:
                    sql = ("INSERT IGNORE INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
                    values = (plate_number, cam_date, cam_time, direction, label, "NEAVIZAT")
                    self.my_cursor.execute(sql, values)
                    self.tms_db.commit()
                    sql = ("INSERT IGNORE INTO reg_visit (nr_auto, data_out, ora_out, visit_status, create_date, lpr_id) VALUES (%s, %s, %s, %s, %s, %s)")
                    values = (plate_number, cam_date, cam_time, "IESIT", datetime.now(), self.last_id[0])
                self.my_cursor.execute(sql, values)
                self.tms_db.commit()

            self.my_cursor.close()
            self.tms_db.close()

    def trailer(self, plate_number, token):
        pass

def run_server():
    server_address = ('', 7080)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print("Server started on port 7080...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()

