import smtplib, ssl
from email.mime.text import MIMEText
try:
    from database.datab import connection, cursor
except:
    mysql_error = messagebox.showerror(title="Connection error", message="Could not connect to DB Server, program will exit")
    quit()

class Parking_notification():
    def __init__(self, id, direction):
        self.id = id
        self.direction = direction

        try:
            connection._open_connection()
            sql = "SELECT * from tauros_park_main WHERE place_id = %s"
            cursor.execute(sql, (self.id,))
            self.result = cursor.fetchall()
            connection.close()

        except:
            print("Error sending email")

        self.subject = f"Tauros Parking Notification - {self.result[0][2]}"
        self.from_addr = "tauros_tasks@tauros.ro"
        self.to_addr = "andrei@tauros.ro"
        self.passwd = "bGrOknm2bm"
        
        if self.direction == "IN":
            self.message = f"""Camionul {self.result[0][2]} a intrat in parcare.\n
                            Nume Sofer: {self.result[0][3]}, {self.result[0][4]}\n
                            Companie: {self.result[0][5]}\n
                            Data si ora intrare: {self.result[0][11]}\n
                            Partener Parcare: {self.result[0][14]}
                            """

            self.send_email(self.message)

        elif self.direction == "OUT":
            self.message = f"""Camionul {self.result[0][2]} a iesit din parcare.\n
                            Nume Sofer: {self.result[0][3]}, {self.result[0][4]}\n
                            Companie: {self.result[0][5]}\n
                            Data si ora intrare: {self.result[0][11]}\n
                            Data si ora iesire: {self.result[0][12]}\n
                            Partener Parcare: {self.result[0][14]}
                            """
            self.send_email(self.message)

    def send_email(self, message):
        msg = MIMEText(message)
        msg['Subject'] = self.subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr

        server = smtplib.SMTP_SSL('mail.tauros.ro', 465)
        # server.starttls()
        server.login(self.from_addr, self.passwd)
        server.sendmail(self.from_addr, self.to_addr, msg.as_string())
        server.quit()

# # Example usage:
# subject = "Test Email"
# message = "This is a test email sent from Python"
# from_addr = "your-email@gmail.com"
# to_addr = "recipient-email@example.com"
# password = "your-email-password"

# send_email(subject, message, from_addr, to_addr, password)

class Tauros_truck_park():
    def __init__(self, id, direction):
        self.id = id
        self.direction = direction

        try:
            connection._open_connection()
            sql = "SELECT * from registru WHERE id = %s"
            cursor.execute(sql, (self.id,))
            self.result = cursor.fetchall()
            connection.close()

        except:
            print("Error sending email")

        self.subject = f"Tauros Parking Notification - {self.result[0][1]}"
        self.from_addr = "tauros_tasks@tauros.ro"
        self.to_addr = "andrei@tauros.ro"
        self.passwd = "bGrOknm2bm"
        
        if self.direction == "IN":
            self.message = f"Camionul {self.result[0][1]} a intrat in parcare."

            self.send_email(self.message)

        elif self.direction == "OUT":
            self.message = f"Camionul {self.result[0][1]} a iesit din parcare."
            
            self.send_email(self.message)

    def send_email(self, message):
        msg = MIMEText(message)
        msg['Subject'] = self.subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr

        server = smtplib.SMTP_SSL('mail.tauros.ro', 465)
        # server.starttls()
        server.login(self.from_addr, self.passwd)
        server.sendmail(self.from_addr, self.to_addr, msg.as_string())
        server.quit()
