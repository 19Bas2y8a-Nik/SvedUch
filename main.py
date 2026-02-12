import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SvedUch - Журнал завуча")
        self.setGeometry(100, 100, 400, 300)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаем layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Добавляем метку
        label = QLabel("Добро пожаловать в SvedUch!")
        layout.addWidget(label)
        
        # Добавляем кнопку
        button = QPushButton("Нажми меня")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
    
    def on_button_clicked(self):
        print("Кнопка нажата!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
