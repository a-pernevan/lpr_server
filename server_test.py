import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
import os
import mysql.connector
import requests
import threading
import time


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
        self.my_cursor.execute("SELECT plate_no from tauros_park_main where plate_no = %s", (plate_number,))
        self.result_samsung = self.my_cursor.fetchall()
        

        if self.result:
            label = "Tauros"
            add_truck = ("INSERT INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
            values = (plate_number, cam_date, cam_time, direction, label, "CHECK")
            self.my_cursor.execute(add_truck, values)
            self.tms_db.commit()
            self.my_cursor.close()
            self.tms_db.close()
            # if direction == "IN":
            #     try:
            #         self.run_turn_led_off_thread()
            #     except:
            #         pass
        elif self.result_samsung:
            label = "Samsung"
            add_truck = ("INSERT INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
            values = (plate_number, cam_date, cam_time, direction, label, "CHECK")
            self.my_cursor.execute(add_truck, values)
            self.tms_db.commit()
            self.my_cursor.close()
            self.tms_db.close()
            # if direction == "IN":
            #     try:
            #         self.run_blink_led_thread()
            #     except:
            #         pass
                        
        else:
            label = "Other"
            add_truck = ("INSERT INTO registru (cap_tractor, data_reg, time_reg, directie, label, token) VALUES (%s, %s, %s, %s, %s, %s)")
            values = (plate_number, cam_date, cam_time, direction, label, "CHECK")
            self.my_cursor.execute(add_truck, values)
            self.tms_db.commit()
            self.my_cursor.close()
            self.tms_db.close()
            # if direction == "IN":
            #     try:
            #         self.run_blink_led_thread()
            #     except:
            #         pass
            # To do - de implementat si iesirile din parcare. 

            # if direction == "OUT":
            #     try:
            #         self.tms_db = mysql.connector.connect(
            #             host = os.getenv("HOST"),
            #             user = os.getenv("USER"),
            #             passwd = os.getenv("PASS"),
            #             database = os.getenv("DB"),
            #             auth_plugin='mysql_native_password'
            #         )
            #     except:
            #         print("Could not connect to MySQL")
            #         quit()
            #     try: 
            #         self.my_cursor = self.tms_db.cursor()
            #         self.my_cursor.execute("SELECT id, cap_tractor from registru WHERE cap_tractor = %s AND token = 'PARKED' AND directie = 'IN'", (plate_number,))
            #         self.result = self.my_cursor.fetchall()
            #         print(self.result)
            #         self.out_id = self.result[0]
            #         self.my_cursor.close()
            #         self.tms_db.close()
            #         if self.result:
            #             try:
            #                 self.tms_db = mysql.connector.connect(
            #                     host = os.getenv("HOST"),
            #                     user = os.getenv("USER"),
            #                     passwd = os.getenv("PASS"),
            #                     database = os.getenv("DB"),
            #                     auth_plugin='mysql_native_password'
            #                 )
            #             except:
            #                 print("Could not connect to MySQL")
            #                 quit()

            #             self.my_cursor = self.tms_db.cursor()
            #             sql = "UPDATE reg_visit SET data_out = %s, ora_out = %s, visit_status = 'IESIT' WHERE lpr_id = %s"
            #             values = (cam_date, cam_time, self.out_id)
            #             self.my_cursor.execute(sql, values)
            #             self.tms_db.commit()
            #             self.my_cursor.close()
            #             self.tms_db.close()
            #     except:
            #         pass
    def trailer(self, plate_number, token):
        pass

def run_server():
    server_address = ('', 7080)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print("Server started on port 7080...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()

