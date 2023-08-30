import csv
import ipaddress
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import time

def upload_file():
    global csv_file_path
    filetypes = [("CSV Files", "*.csv")]
    csv_file_path = filedialog.askopenfilename(filetypes=filetypes)
    if csv_file_path:
        file_label.config(text=f"Selected File: {csv_file_path}")
    else:
        file_label.config(text="No file selected")

def generate_dhcp_config():
    if csv_file_path:
        try:
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                # Get the domain name input
                domain_input_value = domain_input.get()
                if domain_input_value == "Input":
                    domain = domain_entry.get()
                else:
                    domain = None

                dhcp_config_all = ""

                # Loop through the rows in the CSV file
                for row_num, row in enumerate(reader, start=1):
                    # Check the value of 'Purpose' and skip the row if it's not "Data" or "Voice"
                    purpose = row.get('Purpose')
                    if purpose not in ["Data", "Voice"]:
                        continue
                    subnet_input = row['CGN Space']
                    description = row.get('Description')
                    location = row.get('Location / Shelf')

                    # Error handling for an incorrectly written CSV file
                    if not subnet_input:
                        raise ValueError(f"Subnet missing or empty in row {row_num}: {row}")
                    if not description:
                        raise ValueError(f"Description missing or empty in row {row_num}: {row}")
                    if not location:
                        raise ValueError(f"Location missing or empty in row {row_num}: {row}")

                    # Convert the subnet input to an IPv4Network object
                    subnet = ipaddress.IPv4Network(subnet_input)

                    # Initialize an empty dictionary to store the DHCP configuration for the site
                    dhcp_config = {}

                    # Add the subnet address and netmask to the dictionary
                    dhcp_config['subnet'] = str(subnet.network_address)
                    dhcp_config['netmask'] = str(subnet.netmask)

                    # Add the TR69 configuration if selected by the user
                    if tr69_choice.get() == "Yes":
                        dhcp_config['tr69_url'] = f'"{tr69_url_entry.get()}"'
                    else:
                        dhcp_config['tr69_url'] = ""

                    # Get custom DNS servers or use Google's DNS servers as default
                    custom_dns = dns_entry.get()
                    dns_servers = custom_dns if custom_dns else "8.8.8.8, 8.8.4.4"

                    # Get custom lease time or use default lease time
                    custom_lease_time = lease_entry.get()
                    lease_time = custom_lease_time if custom_lease_time else "86400"

                    # Add the default gateway and broadcast address to the dictionary
                    dhcp_config['gateway'] = str(subnet.network_address + 1)
                    dhcp_config['broadcast'] = str(subnet.broadcast_address)

                    # Get custom DNS servers or use Google's DNS servers as default
                    custom_dns = dns_entry.get()
                    if custom_dns:
                        dns_final = custom_dns
                    else:
                        dns_final = "8.8.8.8, 8.8.4.4"

                    # Add the pool name and description to the dictionary
                    dhcp_config['pool_name'] = f"{location} {description}"

                    # Use the domain name from the user input or the CSV file
                    if domain:
                        dhcp_config['domain_name'] = f'"{domain}"'
                    else:
                        default_domain = "default.domain"
                        dhcp_config['domain_name'] = f'"{default_domain}"'

                    # Generate the DHCP configuration for the site
                    ip_range = list(subnet.hosts())[1:-1]
                    start_ip, end_ip = str(ip_range[0]), str(ip_range[-1])
                    end_ip = str(end_ip[:-1])
                    end_ip += str(4)

                    dhcp_config_site = (
 "# {}\n"
    "subnet {} netmask {} {{\n"
    "  pool {{\n"
    "    failover peer \"failover-partner\";\n"
    "    range {} {};\n"
    "    deny dynamic bootp clients;\n"
    "  }}\n"
    "  default-lease-time {};\n"
    "  {}"  #Here are the 2 lines for TR69 if it is enabled in the GUI
    "  {}"
    "  option routers {};\n"
    "  option broadcast-address {};\n"
    "  option subnet-mask {};\n"
    "  option domain-name {};\n"
    f"  option domain-name-servers {dns_final};\n" 
    "}}\n"
).format(
    dhcp_config['pool_name'],
    dhcp_config['subnet'], dhcp_config['netmask'],
    start_ip, end_ip,
    lease_time,
    "vendor-option-space tr69;\n" if tr69_choice.get() == "Yes" else "",
    "option tr69.acs-server-url " + f'"{tr69_url_entry.get()}"' + ";\n" if tr69_choice.get() == "Yes" else "",
    dhcp_config['gateway'],
    dhcp_config['broadcast'],
    dhcp_config['netmask'],
    dhcp_config['domain_name'],
)
                    dhcp_config_all += dhcp_config_site

            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, dhcp_config_all)
            status_label.config(text="DHCP configuration generated successfully.")
        except FileNotFoundError:
            status_label.config(text=f"Error: '{csv_file_path}' does not exist.")
        except ValueError as ve:
            status_label.config(text=f"ValueError: {str(ve)}")
        except Exception as e:
            status_label.config(text=f"An error occurred: {str(e)}")
    else:
        status_label.config(text="No file selected.")

def export_config():
    config_text = output_text.get("1.0", tk.END)
    if config_text:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
# Comment out the First and Third F.write statement below if you want the export file to only contain the generated subnet declerations
                f.write("""
# The ddns-updates-style parameter controls whether or not the server will attempt to do a DNS update when a lease is confirmed. We default to the
# behavior of the version 2 packages ('none', since DHCP v2 didn't have support for DDNS.)
ddns-update-style none;

# option definitions common to all supported networks...
# option domain-name "default.domain";
# option domain-name-servers 8.8.4.4, 8.8.8.8
# failover peer "#failover-partner" {
#        primary;
#        address x.x.x.x;
#        port 647;
#        peer address x.x.x.x;
#        peer port 647;
#        max-response-delay 60;
#        max-unacked-updates 10;
#        mclt 300;
#        split 128;
#        load balance max seconds 3;
#}

INTERFACES="ens224, ens256"; # MUST CHANGE INTERFACES TO REFLECT YOURS
authoritative; # If this DHCP server is the official DHCP server for the local network, the authoritative directive should be uncommented.
default-lease-time 3600;
max-lease-time 86400;
min-lease-time 86400;

#rndc key for load-balance partner relationship
key "rndc-key" {
        algorithm hmac-md5;
        secret "OhJMfORlWpQjHyzsmNGsMXY2VZ6Txe8rMmKYjMm1LlENzoBqXZdNZF0TWjqL5IY5X1Fn5zUAmyEAeKGRbryBAg==";
};

# Use this to send dhcp log messages to a different log file (you also have to hack syslog.conf to complete the redirection).
log-facility local3;

# TR69 option space
option space tr69;
option tr69.acs-server-url code 43 = text;


#Must have empty declaration to listen on, Insert your subnet declerations here

subnet x.x.x.x netmask y.y.y.y {
}

subnet x.x.x.x netmask y.y.y.y {
}
""")
                f.write(config_text)
                f.write(""" 
###  option82 logging ascii

if((option dhcp-message-type = 3 or option dhcp-message-type = 5) and
exists agent.circuit-id) {
    log(info, concat( "OPTION-82 | IP=",
        binary-to-ascii (10, 8, ".",leased-address),
        " | MAC=",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 1, 1))),2),":",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 2, 1))),2),":",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 3, 1))),2),":",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 4, 1))),2),":",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 5, 1))),2),":",
        suffix (concat("0", binary-to-ascii (16, 8, "",
        substring( hardware, 6, 1))),2), " | CIRCUIT-ID=",
        (option agent.circuit-id)));
}

if exists agent.remote-id
{
        log ( info, concat( "OPTION-82 | IP=",
           binary-to-ascii (10, 8, ".", leased-address), " REMOTE-ID=",
           option agent.remote-id));
}                        
""")
            status_label.config(text="DHCP configuration exported successfully.")
        else:
            status_label.config(text="Export canceled.")
    else:
        status_label.config(text="No configuration to export.")

# Create the main window
window = tk.Tk()
window.title("DHCP Configuration Writer")

# Set the background color
window.configure(bg="#333333")

# Configure styles
style = ttk.Style()
style.configure("TButton",
                foreground="black",
                background="#7D3C98",
                font=("Helvetica", 12, "bold"),
                borderwidth=2)
style.configure("TLabel",
                foreground="white",
                background="#333333",
                font=("Helvetica", 12))
style.configure("TFrame",
                background="#333333")
style.configure("TCombobox",
                font=("Helvetica", 12),
                fieldbackground="#333333",
                foreground="black")
style.configure("TEntry",
                font=("Helvetica", 12),
                fieldbackground="#f0f0f0", 
                foreground="#333333", 
                borderwidth=2) 
style.configure("TScrolledText",
                foreground="white",)

# Create a frame for file selection
file_frame = ttk.Frame(window)
file_frame.pack(pady=10)

file_button = ttk.Button(file_frame, text="Select CSV File", command=upload_file)
file_button.grid(row=0, column=0, padx=10)

file_label = ttk.Label(file_frame, text="No file selected")
file_label.grid(row=0, column=1, padx=10)

# Create a frame for domain input
domain_frame = ttk.Frame(window)
domain_frame.pack(pady=10)

domain_label = ttk.Label(domain_frame, text="Input domain name:")
domain_label.grid(row=0, column=0, padx=10)

domain_input = tk.StringVar(value="Use CSV")
domain_dropdown = ttk.Combobox(domain_frame, textvariable=domain_input, values=["Use CSV", "Input"], state="readonly")
domain_dropdown.grid(row=0, column=1, padx=10)

domain_entry = ttk.Entry(domain_frame, width=30) 
domain_entry.grid(row=0, column=2, padx=10)

# Create a frame for TR69 input
tr69_frame = ttk.Frame(window)
tr69_frame.pack(pady=10)

tr69_label = ttk.Label(tr69_frame, text="Include TR69 Configuration:")
tr69_label.grid(row=0, column=0, padx=10)

tr69_choice = tk.StringVar(value="No")
tr69_radio_yes = ttk.Radiobutton(tr69_frame, text="Yes", variable=tr69_choice, value="Yes")
tr69_radio_yes.grid(row=0, column=1, padx=10)

tr69_radio_no = ttk.Radiobutton(tr69_frame, text="No", variable=tr69_choice, value="No")
tr69_radio_no.grid(row=0, column=2, padx=10)

tr69_url_label = ttk.Label(tr69_frame, text="TR69 URL:")
tr69_url_label.grid(row=1, column=0, padx=10)

tr69_url_entry = ttk.Entry(tr69_frame, width=30)  
tr69_url_entry.grid(row=1, column=1, columnspan=2, padx=10)

# Create a frame for DNS input
dns_frame = ttk.Frame(window)
dns_frame.pack(pady=10)

dns_label = ttk.Label(dns_frame, text="Custom DNS Servers (comma-separated):")
dns_label.grid(row=0, column=0, padx=10)

dns_entry = ttk.Entry(dns_frame, width=30)  
dns_entry.grid(row=0, column=1, padx=10)

# Create a frame for Lease Time input
lease_frame = ttk.Frame(window)
lease_frame.pack(pady=10)

lease_label = ttk.Label(lease_frame, text="Custom Lease Time (seconds):")
lease_label.grid(row=0, column=0, padx=10)

lease_entry = ttk.Entry(lease_frame, width=10) 
lease_entry.grid(row=0, column=1, padx=10)

# Create a button to generate DHCP configuration
generate_button = ttk.Button(window, text="Generate DHCP Config", command=generate_dhcp_config)
generate_button.pack(pady=10)

# Create a button to export the DHCP configuration
export_button = ttk.Button(window, text="Export Config", command=export_config)
export_button.pack(pady=10)

# Create a status label
status_label = ttk.Label(window, text="")
status_label.pack()

# Create a frame for the output text box
output_frame = ttk.Frame(window)
output_frame.pack(pady=10)

output_label = ttk.Label(output_frame, text="DHCP Configuration:")
output_label.pack()

# Create a scrolled text box to display the DHCP configuration
output_text = scrolledtext.ScrolledText(output_frame, height=30, width=60, bg="#929292")
output_text.pack()

# Configure the foreground color of the text inside the output_text widget
output_text.config(foreground="white")

# Run the main event loop
window.mainloop()
