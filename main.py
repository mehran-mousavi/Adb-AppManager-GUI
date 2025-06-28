import sys
import subprocess
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor

class AdbWorker(QThread):
    output = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.check_output(self.command, shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            result = e.output
        self.output.emit(result)

class AndroidAppManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android App Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget {
                color: #ffffff;
                background-color: #3c3f41;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4c5052;
            }
            QTableWidget {
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.all_apps = []  # Store all apps for filtering
        self.workers = []  # Keep track of all running workers
        self.all_apps_output = ""  # Initialize the attribute to store all apps output
        self.uad_info = {}  # Will map package name to info
        self.load_uad_lists()
        self.setup_ui()

    def load_uad_lists(self):
        try:
            with open("uad_lists.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    if "id" in entry:
                        self.uad_info[entry["id"]] = entry
        except Exception as e:
            print(f"Failed to load uad_lists.json: {e}")

    def setup_ui(self):
        # Device selection
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        # Add event listener for device selection change
        self.device_combo.currentIndexChanged.connect(lambda: (self.all_apps.clear(), self.app_table.setRowCount(0), self.app_table.clearContents(), self.update_device_info(), self.load_all_apps()))
        self.refresh_devices_btn = QPushButton("Refresh Devices")
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(QLabel("Select Device:"))
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_devices_btn)
        device_layout.addStretch()
        self.layout.addLayout(device_layout)

        # Device info
        self.device_info_label = QLabel("Device Info: Not connected")
        self.layout.addWidget(self.device_info_label)

        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search apps...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_apps)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        self.layout.addLayout(search_layout)

        # App list
        self.app_table = QTableWidget()
        self.app_table.setColumnCount(4)
        self.app_table.setHorizontalHeaderLabels(["App Name", "Package Name", "Status", "Type"])
        self.app_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)  # Change selection to row
        self.layout.addWidget(self.app_table)
        self.app_table.itemSelectionChanged.connect(self.update_app_desc)

        # App description area (moved below the grid)
        self.app_desc_label = QLabel()
        self.app_desc_label.setWordWrap(True)
        self.app_desc_label.setMinimumHeight(80)
        self.app_desc_label.setStyleSheet("background-color: #232629; color: #ffffff; border: 1px solid #555555; padding: 8px; border-radius: 3px;")
        self.layout.addWidget(self.app_desc_label)
        self.clear_app_desc()

        # Action buttons
        action_layout = QHBoxLayout()
        self.enable_btn = QPushButton("Enable")
        self.disable_btn = QPushButton("Disable")
        self.uninstall_btn = QPushButton("Uninstall")
        self.enable_btn.clicked.connect(self.enable_app)
        self.disable_btn.clicked.connect(self.disable_app)
        self.uninstall_btn.clicked.connect(self.uninstall_app)
        action_layout.addWidget(self.enable_btn)
        action_layout.addWidget(self.disable_btn)
        action_layout.addWidget(self.uninstall_btn)
        self.layout.addLayout(action_layout)

        self.refresh_devices()

    def clear_app_desc(self):
        self.app_desc_label.setText("<b>App Description:</b><br>Select an app to see details.")
        self.app_desc_label.setStyleSheet("background-color: #232629; color: #ffffff; border: 1px solid #555555; padding: 8px; border-radius: 3px;")

    def update_app_desc(self):
        selected_items = self.app_table.selectedItems()
        if not selected_items:
            self.clear_app_desc()
            return
        row = selected_items[0].row()
        package = self.app_table.item(row, 1).text()
        info = self.uad_info.get(package)
        if not info:
            self.app_desc_label.setText(f"<b>App Description:</b><br>No info available for <code>{package}</code>.")
            self.app_desc_label.setStyleSheet("background-color: #232629; color: #ffffff; border: 1px solid #555555; padding: 8px; border-radius: 3px;")
            return
        app_type = info.get("list", "Unknown")
        desc = info.get("description", "No description available.")
        removal = info.get("removal", "Recommended")
        if removal == "Recommended":
            removal_text = "<span style='color:#4CAF50;font-weight:bold;'>Recommended: Safe to remove this app.</span>"
        elif removal == "Advanced":
            removal_text = "<span style='color:#FFA500;font-weight:bold;'>Important package. Removal is only recommended for advanced users.</span>"
        elif removal == "Expert":
            removal_text = "<span style='color:#F44336;font-weight:bold;'>Critical package. Removing this may cause your device to become unusable (bricked).</span>"
        else:
            removal_text = f"<span>{removal}</span>"
        html = f"""
        <b style='font-weight:bold;margin-bottom:4px;'>App Type:</b> {app_type}<br>
        <b style='font-weight:bold;margin-bottom:4px;'>Description:</b> {desc}<br>
        <b style='font-weight:bold;margin-bottom:4px;'>Removal:</b> {removal_text}
        """
        self.app_desc_label.setText(html)
        self.app_desc_label.setStyleSheet("background-color: #232629; color: #ffffff; border: 1px solid #555555; padding: 8px; border-radius: 3px;")

    def run_adb_command(self, command, callback):
        worker = AdbWorker(command)
        worker.output.connect(callback)
        worker.finished.connect(lambda: self.workers.remove(worker))  # Remove worker from list when done
        self.workers.append(worker)
        worker.start()

    def refresh_devices(self):
        self.device_combo.clear()
        print("Refreshing devices...")
        self.run_adb_command("adb devices", self.update_device_list)

    def update_device_list(self, output):
        print(f"ADB output: {output}")
        devices = []
        for line in output.strip().split('\n')[1:]:
            if '\t' in line:
                device, status = line.split('\t')
                if status == 'device':
                    devices.append(device)
        print(f"Detected devices: {devices}")
        self.device_combo.addItems(devices)
        if devices:
            self.device_combo.setCurrentIndex(0)
            # self.update_device_info()
            # self.load_all_apps()  # Load all apps when a device is selected
        else:
            self.all_apps = []  # Clear the apps list
            self.app_table.setRowCount(0)  # Clear the displayed rows in the app table
            self.app_table.clearContents()  # Remove all items from the app table
            print("No devices detected")

    def update_device_info(self):
        device = self.device_combo.currentText()
        if device:
            self.run_adb_command(f"adb -s {device} shell getprop", self.display_device_info)

    def display_device_info(self, output):
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()[1:-1]] = value.strip()[1:-1]

        device_info = f"Model: {info.get('ro.product.model', 'Unknown')}\t\t"
        device_info += f"Android Version: {info.get('ro.build.version.release', 'Unknown')}\t\t"
        device_info += f"API Level: {info.get('ro.build.version.sdk', 'Unknown')}"
        self.device_info_label.setText(f"Device Info:\n\n{device_info}")

    def load_all_apps(self):
        device = self.device_combo.currentText()
        if device:
            self.all_apps = []  # Clear the apps list
            self.app_table.setRowCount(0)  # Clear the displayed rows in the app table
            self.app_table.clearContents()  # Remove all items from the app table
            self.run_adb_command(f"adb -s {device} shell pm list packages -f -u", self.store_all_apps_output)

    def store_all_apps_output(self, output):
        self.all_apps_output = output  # Store the output for later use
        self.store_all_apps()

    def store_all_apps(self):
        self.all_apps = []
        device = self.device_combo.currentText()
        if device:
            # Run the command to get disabled packages in a separate thread
            self.run_adb_command(f"adb -s {device} shell pm list packages -d", self.process_disabled_packages)

    def process_disabled_packages(self, disabled_output):
        disabled_packages = set(line.split(':')[1] for line in disabled_output.strip().split('\n') if line)
        for line in self.all_apps_output.strip().split('\n'):
            if '=' in line:
                path, package = line.rsplit('=', 1)
                app_name = package.split('.')[-1]
                status = "Disabled" if package in disabled_packages else "Enabled"
                app_type = "System" if "/system/" in path else "User"
                self.all_apps.append((app_name, package, status, app_type))
        self.display_apps(self.all_apps)

    def display_apps(self, apps):
        self.app_table.setRowCount(0)
        for app_name, package, status, app_type in apps:
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)
            self.app_table.setItem(row, 0, QTableWidgetItem(app_name))
            self.app_table.setItem(row, 1, QTableWidgetItem(package))
            self.app_table.setItem(row, 2, QTableWidgetItem(status))
            self.app_table.setItem(row, 3, QTableWidgetItem(app_type))
            if status == "Disabled":
                for col in range(4):
                    self.app_table.item(row, col).setBackground(QColor(244, 67, 54))  # Material Red


    def search_apps(self):
        query = self.search_input.text().lower()
        filtered_apps = [app for app in self.all_apps if query in app[1].lower()]
        self.display_apps(filtered_apps)

    def get_app_status(self, package):
        device = self.device_combo.currentText()
        result = subprocess.check_output(f"adb -s {device} shell pm list packages -d", shell=True, text=True)
        return "Disabled" if package in result else "Enabled"

    def enable_app(self):
        self.change_app_state("enable")

    def disable_app(self):
        self.change_app_state("disable")

    def change_app_state(self, action):
        device = self.device_combo.currentText()
        if not device:
            QMessageBox.warning(self, "Error", "No device selected")
            return

        selected_items = self.app_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No app selected")
            return

        package = self.app_table.item(selected_items[0].row(), 1).text()
        command = f"adb -s {device} shell pm {action}{'-user' if action == 'disable' else ''} {package}"
        self.run_adb_command(command, lambda _: QTimer.singleShot(1000, self.load_all_apps))  # Delay before refreshing

    def uninstall_app(self):
        device = self.device_combo.currentText()
        if not device:
            QMessageBox.warning(self, "Error", "No device selected")
            return

        selected_items = self.app_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No app selected")
            return

        row = selected_items[0].row()
        package = self.app_table.item(row, 1).text()
        app_type = self.app_table.item(row, 3).text()

        if app_type == "System":
            reply = QMessageBox.warning(self, "Warning",
                                        "You are about to uninstall a system app. This may cause system instability. "
                                        "Are you sure you want to proceed?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        command = f"adb -s {device} shell pm uninstall --user 0 {package}"
        self.run_adb_command(command, lambda _: QTimer.singleShot(1000, self.load_all_apps))

    def closeEvent(self, event):
        for worker in self.workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AndroidAppManager()
    window.show()
    sys.exit(app.exec_())
