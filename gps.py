import serial

# Define the field indices for GPGGA
GPGGA_FIELDS = {
    "msg_id": 0,
    "utc": 1,
    "latitude": 2,
    "NorS": 3,
    "longitude": 4,
    "EorW": 5,
    "pos_indi": 6,
    "total_Satellite": 7,
}

def parse_gpgga(sentence):
    fields = sentence.split(",")
    if fields[GPGGA_FIELDS["msg_id"]] == "$GPGGA":
        utc_str = fields[GPGGA_FIELDS["utc"]]
        lat_str = fields[GPGGA_FIELDS["latitude"]]
        lon_str = fields[GPGGA_FIELDS["longitude"]]

        if utc_str and lat_str and lon_str:
            # Parse UTC time
            h = int(utc_str[0:2])
            m = int(utc_str[2:4])
            s = float(utc_str[4:])
            utc_time = f"{h:02}:{m:02}:{s:06.3f}"

            # Parse Latitude
            lat_d = int(lat_str[:2])
            lat_m = float(lat_str[2:])
            latitude = lat_d + (lat_m / 60)
            if fields[GPGGA_FIELDS["NorS"]] == "S":
                latitude = -latitude

            # Parse Longitude
            lon_d = int(lon_str[:3])
            lon_m = float(lon_str[3:])
            longitude = lon_d + (lon_m / 60)
            if fields[GPGGA_FIELDS["EorW"]] == "W":
                longitude = -longitude

            return utc_time, latitude, longitude
    return None

def read_gps_data(port, baudrate, output_file):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser, open(output_file, 'w') as file:
            file.write("UTC Time,Latitude,Longitude\n")
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('ascii', errors='replace').strip()
                    if line.startswith("$GPGGA"):
                        parsed_data = parse_gpgga(line)
                        if parsed_data:
                            utc_time, latitude, longitude = parsed_data
                            file.write(f"{utc_time},{latitude},{longitude}\n")
                            print(f"UTC Time: {utc_time}, Latitude: {latitude}, Longitude: {longitude}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    gps_port = "/dev/ttyS0"  # Adjust the port name as needed
    baud_rate = 9600  # or your desired baud rate
    output_file = "gps_data.txt"
    read_gps_data(gps_port, baud_rate, output_file)