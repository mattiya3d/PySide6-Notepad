from sys import argv
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow

def main():
    app = QApplication(argv)
    
    # Keep it simple, no custom arguments passed here
    mainwindow = MainWindow()
    mainwindow.show()
    
    app.exec()

if __name__ == "__main__":
    main()