import sys
import math
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLineEdit, QLabel, QListWidget, QCheckBox, QGridLayout, QColorDialog,
    QFileDialog, QRadioButton, QSpinBox, QComboBox, QGroupBox, QMenuBar,
    QAction, QMainWindow, QTextBrowser, QDialog, QSplitter, QScrollArea
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import Qt
import subprocess
import os.path

SETTINGS_FILE = "settings.json"
ABOUT_FILE = "about.html"
USER_GUIDE_CHM_FILE = "particle_sim.chm"

class HelpDialog(QDialog):
    def __init__(self, title, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)

        layout = QVBoxLayout()
        self.browser = QTextBrowser()
        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

class ParticleEditDialog(QDialog):
    def __init__(self, particle, parent=None):
        super().__init__(parent)
        self.particle = particle
        self.setWindowTitle("Редактировать частицу")
        self.resize(500, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create form layout for particle properties
        form_layout = QGridLayout()

        # Create input fields with current particle values
        self.posx_input = QLineEdit(str(self.particle.x_mass[0]))
        self.posy_input = QLineEdit(str(self.particle.y_mass[0]))
        self.charge_input = QLineEdit(str(self.particle.charge))
        self.mass_input = QLineEdit(str(self.particle.mass))
        self.velocity_input = QLineEdit(str(self.particle.velocity))
        self.angle_input = QLineEdit(str(self.particle.angle))
        self.dt_input = QLineEdit(str(self.particle.dt))

        # Add labels and inputs to form
        labels = ["Позиция X", "Позиция Y", "Заряд", "Масса", "Скорость", "Угол", "dt"]
        inputs = [self.posx_input, self.posy_input, self.charge_input,
                 self.mass_input, self.velocity_input, self.angle_input, self.dt_input]

        for i, (label, input_field) in enumerate(zip(labels, inputs)):
            form_layout.addWidget(QLabel(label), i, 0)
            form_layout.addWidget(input_field, i, 1)

        # Add checkboxes for interactions
        self.ch_interact_check = QCheckBox("Электрическое взаимодействие")
        self.mass_interact_check = QCheckBox("Гравитационное взаимодействие")
        self.ch_interact_check.setChecked(self.particle.is_moving_ch)
        self.mass_interact_check.setChecked(self.particle.is_moving_m)

        form_layout.addWidget(self.ch_interact_check, len(labels), 0)
        form_layout.addWidget(self.mass_interact_check, len(labels), 1)

        # Add color selection button
        self.current_color = self.particle.color
        self.color_btn = QPushButton("Выбрать цвет")
        self.color_btn.setStyleSheet(f"background-color: {self.current_color}")
        self.color_btn.clicked.connect(self.choose_color)
        form_layout.addWidget(QLabel("Цвет:"), len(labels) + 1, 0)
        form_layout.addWidget(self.color_btn, len(labels) + 1, 1)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Add buttons for save/cancel
        button_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить изменения")
        cancel_button = QPushButton("Отмена")

        save_button.clicked.connect(self.save_changes)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.current_color))
        if color.isValid():
            self.current_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.current_color}")

    def save_changes(self):
        try:
            # Get values from input fields
            posx = float(self.posx_input.text())
            posy = float(self.posy_input.text())
            charge = float(self.charge_input.text())
            mass = float(self.mass_input.text())
            velocity = float(self.velocity_input.text())
            angle = float(self.angle_input.text())
            dt = float(self.dt_input.text())

            # Update particle properties
            self.particle.charge = charge
            self.particle.mass = mass
            self.particle.is_moving_ch = self.ch_interact_check.isChecked()
            self.particle.is_moving_m = self.mass_interact_check.isChecked()
            self.particle.dt = dt
            self.particle.color = self.current_color
            self.particle.velocity = velocity
            self.particle.angle = angle

            # Update position and velocity
            rad_angle = math.radians(angle)
            self.particle.vx = velocity * np.cos(rad_angle)
            self.particle.vy = velocity * np.sin(rad_angle)

            # Reset trajectory to start from new position
            self.particle.x_mass = [posx, posx + self.particle.vx * dt]
            self.particle.y_mass = [posy, posy + self.particle.vy * dt]

            self.accept()
        except ValueError as e:
            # Show error message if input validation fails
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка ввода", f"Пожалуйста, введите корректные числовые значения: {str(e)}")

class Particle:
    def __init__(self, posx, posy, charge, mass, velocity, angle, dt, is_moving_ch, is_moving_m, color='blue', max_points=1000):
        self.charge = charge
        self.mass = mass
        self.is_moving_ch = is_moving_ch
        self.is_moving_m = is_moving_m
        self.dt = dt
        self.color = color
        self.max_points = max_points
        rad_angle = math.radians(angle)
        self.x_mass = [posx, posx + velocity * np.cos(rad_angle) * dt]
        self.y_mass = [posy, posy + velocity * np.sin(rad_angle) * dt]
        self.ax = 0
        self.ay = 0
        self.vx = velocity * np.cos(rad_angle)
        self.vy = velocity * np.sin(rad_angle)
        self.velocity = velocity
        self.angle = angle
        self.vx_history = [self.vx,self.vx]
        self.vy_history = [self.vy,self.vy]
        self.x_mass_init = [posx, posx + velocity * np.cos(rad_angle) * dt]
        self.y_mass_init = [posy, posy + velocity * np.sin(rad_angle) * dt]
    def __str__(self):
        return (f"Позиция: ({self.x_mass[-1]:.2f}, {self.y_mass[-1]:.2f}), "
                f"Заряд={self.charge}, масса={self.mass}, Скорость={self.velocity}, "
                f"угол={self.angle}, dt={self.dt}, "
                f"Уч_эл={self.is_moving_ch}, Уч_грав={self.is_moving_m}, Цвет={self.color}")

    def to_dict(self):
        return {
            "posx": self.x_mass[0],
            "posy": self.y_mass[0],
            "charge": self.charge,
            "mass": self.mass,
            "velocity": self.velocity,
            "angle": self.angle,
            "dt": self.dt,
            "is_moving_ch": self.is_moving_ch,
            "is_moving_m": self.is_moving_m,
            "color": self.color,
            "max_points": self.max_points
        }

    @staticmethod
    def from_dict(data):
        return Particle(**data)

    def add_point(self, x, y, use_limits=True):
        self.x_mass.append(x)
        self.y_mass.append(y)

        # Trim arrays if they exceed max_points
        if use_limits and len(self.x_mass) > self.max_points:
            self.x_mass = self.x_mass[-self.max_points:]
            self.y_mass = self.y_mass[-self.max_points:]
    def add_v(self,vx,vy):
        self.vx_history.append(vx)
        self.vy_history.append(vy)
class ParticleSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симулятор частиц")
        self.resize(1600, 800)
        self.particles = []
        self.constants = {
            "G": 1.0,
            "k": 1.0,
            "tneeded": 10.0,
            "max_points": 1000,
            "use_point_limits": False,
            "grid_size_x": 100,
            "grid_size_y": 100
        }
        self.load_settings()
        self.initUI()

    def initUI(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Main horizontal layout to split controls and graph
        main_layout = QHBoxLayout(central_widget)

        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left side - Controls
        left_widget = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)
        left_layout = QVBoxLayout(left_widget)

        # Right side - Graph and visualization controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Add widgets to splitter
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_widget)

        # Set initial sizes (controls take about 40%, graph 60%)
        splitter.setSizes([400, 600])

        # ===== LEFT SIDE - CONTROLS =====

        # Particle parameters
        param_group = QGroupBox("Параметры частицы")
        grid = QGridLayout()
        labels = ["X", "Y", "Заряд", "Масса", "Скорость", "Угол", "dt"]
        self.inputs = [QLineEdit("0") for _ in labels]
        for i, label in enumerate(labels):
            grid.addWidget(QLabel(label), 0, i)
            grid.addWidget(self.inputs[i], 1, i)
        # Set default values for specific fields
        self.inputs[3].setText("1")      # Mass = 1
        self.inputs[4].setText("1")      # Velocity = 1
        self.inputs[6].setText("0.0001") # dt = 0.0001
        self.color_btn = QPushButton("Выбрать цвет")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = "blue"
        grid.addWidget(self.color_btn, 1, len(labels))

        self.ch_interact_check = QCheckBox("Электрическое взаимодействие")
        self.mass_interact_check = QCheckBox("Гравитационное взаимодействие")
        self.ch_interact_check.setChecked(True)
        self.mass_interact_check.setChecked(False)

        grid.addWidget(self.ch_interact_check, 2, 0, 1, 3)
        grid.addWidget(self.mass_interact_check, 2, 3, 1, 3)
        param_group.setLayout(grid)
        left_layout.addWidget(param_group)

        # Constants
        const_group = QGroupBox("Константы симуляции")
        const_layout = QGridLayout()

        const_layout.addWidget(QLabel("G:"), 0, 0)
        self.g_input = QLineEdit(str(self.constants["G"]))
        const_layout.addWidget(self.g_input, 0, 1)

        const_layout.addWidget(QLabel("k:"), 0, 2)
        self.k_input = QLineEdit(str(self.constants["k"]))
        const_layout.addWidget(self.k_input, 0, 3)

        const_layout.addWidget(QLabel("Время симуляции:"), 1, 0)
        self.t_input = QLineEdit(str(self.constants["tneeded"]))
        const_layout.addWidget(self.t_input, 1, 1)

        # Add max points control
        const_layout.addWidget(QLabel("Макс. точек траектории:"), 1, 2)
        self.max_points_input = QSpinBox()
        self.max_points_input.setRange(10, 1000000)
        self.max_points_input.setValue(self.constants["max_points"])
        const_layout.addWidget(self.max_points_input, 1, 3)

        self.use_limits_check = QCheckBox("Использовать ограничение траектории")
        self.use_limits_check.setChecked(self.constants["use_point_limits"])
        const_layout.addWidget(self.use_limits_check, 2, 0, 1, 4)

        # Add grid size controls for heatmap
        const_layout.addWidget(QLabel("Размер сетки X:"), 3, 0)
        self.grid_size_x_input = QSpinBox()
        self.grid_size_x_input.setRange(10, 1000)
        self.grid_size_x_input.setValue(self.constants["grid_size_x"])
        const_layout.addWidget(self.grid_size_x_input, 3, 1)

        const_layout.addWidget(QLabel("Размер сетки Y:"), 3, 2)
        self.grid_size_y_input = QSpinBox()
        self.grid_size_y_input.setRange(10, 1000)
        self.grid_size_y_input.setValue(self.constants["grid_size_y"])
        const_layout.addWidget(self.grid_size_y_input, 3, 3)

        const_group.setLayout(const_layout)
        left_layout.addWidget(const_group)

        # Particle management buttons
        btn_group = QGroupBox("Управление частицами")
        btn_layout = QGridLayout()

        self.add_btn = QPushButton("Добавить частицу")
        self.edit_btn = QPushButton("Редактировать частицу")  # Add this line
        self.delete_btn = QPushButton("Удалить частицу")
        self.clear_btn = QPushButton("Очистить частицы")
        self.save_btn = QPushButton("Сохранить частицы")
        self.load_btn = QPushButton("Загрузить частицы")
        self.move_up_btn = QPushButton("Вверх")
        self.move_down_btn = QPushButton("Вниз")

        btn_layout.addWidget(self.add_btn, 0, 0)
        btn_layout.addWidget(self.edit_btn, 0, 1)
        btn_layout.addWidget(self.delete_btn, 0, 2)
        btn_layout.addWidget(self.clear_btn, 0, 3)
        btn_layout.addWidget(self.save_btn, 1, 0)
        btn_layout.addWidget(self.load_btn, 1, 1)
        btn_layout.addWidget(self.move_up_btn, 1, 2)
        btn_layout.addWidget(self.move_down_btn, 1, 3)

        btn_group.setLayout(btn_layout)
        left_layout.addWidget(btn_group)

        # Particle list
        list_group = QGroupBox("Частицы")
        list_layout = QVBoxLayout()
        self.particle_list = QListWidget()
        list_layout.addWidget(self.particle_list)
        list_group.setLayout(list_layout)
        left_layout.addWidget(list_group)

        # Real-world time conversion section
        real_world_group = QGroupBox("Конвертация реального времени")
        real_world_layout = QGridLayout()

        # Input fields for real-world values
        real_world_layout.addWidget(QLabel("Реальная масса 1 (кг):"), 0, 0)
        self.real_mass1_input = QLineEdit("9.1e-31")  # Default: electron mass
        real_world_layout.addWidget(self.real_mass1_input, 0, 1)

        real_world_layout.addWidget(QLabel("Реальная масса 2 (кг):"), 1, 0)
        self.real_mass2_input = QLineEdit("1.67e-27")  # Default: proton mass
        real_world_layout.addWidget(self.real_mass2_input, 1, 1)

        real_world_layout.addWidget(QLabel("Реальное расстояние (м):"), 2, 0)
        self.real_distance_input = QLineEdit("5.3e-11")  # Default: Bohr radius
        real_world_layout.addWidget(self.real_distance_input, 2, 1)

        real_world_layout.addWidget(QLabel("Реальный заряд 1 (Кл):"), 3, 0)
        self.real_charge1_input = QLineEdit("1.6e-19")  # Default: elementary charge
        real_world_layout.addWidget(self.real_charge1_input, 3, 1)

        real_world_layout.addWidget(QLabel("Реальный заряд 2 (Кл):"), 4, 0)
        self.real_charge2_input = QLineEdit("1.6e-19")  # Default: elementary charge
        real_world_layout.addWidget(self.real_charge2_input, 4, 1)

        # Output fields for real-world time
        real_world_layout.addWidget(QLabel("Электростатическое время (с):"), 5, 0)
        self.electrostatic_time_output = QLabel("0.0")
        real_world_layout.addWidget(self.electrostatic_time_output, 5, 1)

        real_world_layout.addWidget(QLabel("Гравитационное время (с):"), 6, 0)
        self.gravitational_time_output = QLabel("0.0")
        real_world_layout.addWidget(self.gravitational_time_output, 6, 1)

        # Calculate button
        self.calc_real_time_btn = QPushButton("Рассчитать реальное время")
        self.calc_real_time_btn.clicked.connect(self.calculate_real_times)
        real_world_layout.addWidget(self.calc_real_time_btn, 7, 0, 1, 2)

        real_world_group.setLayout(real_world_layout)
        left_layout.addWidget(real_world_group)

        # Add a stretch to push everything up
        left_layout.addStretch()

        # ===== RIGHT SIDE - GRAPH AND VISUALIZATION CONTROLS =====

        # Visualization options
        viz_group = QGroupBox("Настройки визуализации")
        viz_layout = QVBoxLayout()

        # Create sub-groups for better organization
        sim_mode_group = QGroupBox("Режим симуляции")
        sim_mode_layout = QHBoxLayout()
        self.real_time_radio = QRadioButton("Симуляция в реальном времени")
        self.default_radio = QRadioButton("Стандартная симуляция")
        self.default_radio.setChecked(True)
        sim_mode_layout.addWidget(self.real_time_radio)
        sim_mode_layout.addWidget(self.default_radio)
        sim_mode_group.setLayout(sim_mode_layout)
        viz_layout.addWidget(sim_mode_group)

        # Integration method group
        method_group = QGroupBox("Метод интегрирования")
        method_layout = QHBoxLayout()
        self.verlet_radio = QRadioButton("Верле")
        self.leapfrog_radio = QRadioButton("Leapfrog")
        self.rk4_radio = QRadioButton("Рунге-Кутт 4 порядка")
        self.bs_radio = QRadioButton("Булирш-Стоер")
        self.verlet_radio.setChecked(True)  # Default to Verlet
        method_layout.addWidget(self.verlet_radio)
        method_layout.addWidget(self.leapfrog_radio)
        method_layout.addWidget(self.rk4_radio)
        method_layout.addWidget(self.bs_radio)
        method_group.setLayout(method_layout)
        viz_layout.addWidget(method_group)

        # Visualization type group
        viz_type_group = QGroupBox("Тип визуализации")
        energy_settings_group = QGroupBox("Настройки энергии")
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(QLabel("Целевая энергия:"))
        self.target_energy_input = QLineEdit("-1.0")  # Default value
        energy_layout.addWidget(self.target_energy_input)
        energy_settings_group.setLayout(energy_layout)
        viz_layout.addWidget(energy_settings_group)
        viz_type_layout = QVBoxLayout()

        # Горизонтальный layout для комбобокса
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Тип:"))
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems([
            "Линии траекторий",
            "Тепловая карта плотности",
            "Гистограмма по оси X",
            "Гистограмма по оси Y",
            "График энергии электрического взаимодействия",
            "График энергии гравитационного взаимодействия",
            "График энергии электрического взаимодействия (приближение)",
            "График энергии гравитационного взаимодействия (приближение)"
        ])
        combo_layout.addWidget(self.viz_type_combo)
        viz_type_layout.addLayout(combo_layout)

        # Добавляем чекбокс для остановки итераций
        self.stop_after_viz_check = QCheckBox("Остановить итерации для тепловой карты и гистограмм")
        self.stop_after_viz_check.setChecked(True)  # По умолчанию активен
        viz_type_layout.addWidget(self.stop_after_viz_check)

        viz_type_group.setLayout(viz_type_layout)
        viz_layout.addWidget(viz_type_group)

        # Run simulation button
        self.sim_btn = QPushButton("Запустить симуляцию")
        viz_layout.addWidget(self.sim_btn)

        viz_group.setLayout(viz_layout)
        right_layout.addWidget(viz_group)

        # Canvas for the plot
        self.canvas = FigureCanvas(plt.figure())
        right_layout.addWidget(self.canvas)

        # Add Reset Simulation button
        self.reset_btn = QPushButton("Сбросить симуляцию")
        self.reset_btn.clicked.connect(self.reset_simulation)
        right_layout.addWidget(self.reset_btn)

        # Adding Pause and Periodicity SpinBox
        self.pause_btn = QPushButton("Пауза")
        self.periodicity_label = QLabel("Период обновления (итераций):")
        self.periodicity_spin = QSpinBox()
        self.periodicity_spin.setRange(1, 1000)
        self.periodicity_spin.setValue(10)

        pause_layout = QHBoxLayout()
        pause_layout.addWidget(self.pause_btn)
        pause_layout.addWidget(self.periodicity_label)
        pause_layout.addWidget(self.periodicity_spin)
        right_layout.addLayout(pause_layout)

        self.add_btn.clicked.connect(self.add_particle)
        self.edit_btn.clicked.connect(self.edit_particle)
        self.delete_btn.clicked.connect(self.delete_particle)
        self.clear_btn.clicked.connect(self.clear_particles)
        self.sim_btn.clicked.connect(self.run_simulation)
        self.save_btn.clicked.connect(self.save_particles_to_file)
        self.load_btn.clicked.connect(self.load_particles_from_file)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.move_up_btn.clicked.connect(self.move_particle_up)
        self.move_down_btn.clicked.connect(self.move_particle_down)

        self.add_default_particles()

        # Variables for pausing and periodicity control
        self.is_paused = False
        self.update_period = 10  # default period
        self.edit_btn.clicked.connect(self.edit_particle)
        self.delete_btn.clicked.connect(self.delete_particle)  # Add this line

    def delete_particle(self):
        # Get the selected particle from the list
        selected_items = self.particle_list.selectedItems()
        if not selected_items:
            return  # No particle selected

        # Get the index of the selected particle
        selected_index = self.particle_list.currentRow()
        if selected_index < 0 or selected_index >= len(self.particles):
            return

        # Remove the particle from the list
        self.particles.pop(selected_index)

        # Update the particle list display
        self.update_particle_list()

        # Clear the canvas and redraw if needed
        # self.canvas.figure.clear()
        # self.canvas.draw()
    def move_particle_up(self):
        """Move the selected particle up in the list"""
        # Get the selected particle index
        selected_index = self.particle_list.currentRow()

        # Check if a particle is selected and it's not already at the top
        if selected_index <= 0 or selected_index >= len(self.particles):
            return

        # Swap the particle with the one above it
        self.particles[selected_index], self.particles[selected_index-1] = \
            self.particles[selected_index-1], self.particles[selected_index]

        # Update the particle list display
        self.update_particle_list()

        # Keep the same particle selected
        self.particle_list.setCurrentRow(selected_index-1)

    def move_particle_down(self):
        """Move the selected particle down in the list"""
        # Get the selected particle index
        selected_index = self.particle_list.currentRow()

        # Check if a particle is selected and it's not already at the bottom
        if selected_index < 0 or selected_index >= len(self.particles) - 1:
            return

        # Swap the particle with the one below it
        self.particles[selected_index], self.particles[selected_index+1] = \
            self.particles[selected_index+1], self.particles[selected_index]

        # Update the particle list display
        self.update_particle_list()

        # Keep the same particle selected
        self.particle_list.setCurrentRow(selected_index+1)
# Then add the edit_particle method to the ParticleSimulator class:
    def edit_particle(self):
        # Get the selected particle from the list
        selected_items = self.particle_list.selectedItems()
        if not selected_items:
            return  # No particle selected

        # Get the index of the selected particle
        selected_index = self.particle_list.currentRow()
        if selected_index < 0 or selected_index >= len(self.particles):
            return

        # Get the particle to edit
        particle = self.particles[selected_index]

        # Create and show the edit dialog
        dialog = ParticleEditDialog(particle, self)
        result = dialog.exec_()

        # If the dialog was accepted (user clicked Save), update the particle list
        if result == QDialog.Accepted:
            self.update_particle_list()

            # Clear the canvas and redraw if needed
            self.canvas.figure.clear()


    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()

    def add_particle(self):
        try:
            values = [float(inp.text()) for inp in self.inputs]
            x, y, q, m, v, angle, dt = values
            color = self.current_color
            max_points = self.max_points_input.value()
            p = Particle(x, y, q, m, v, angle, dt,
                         self.ch_interact_check.isChecked(),
                         self.mass_interact_check.isChecked(),
                         color, max_points)
            self.particles.append(p)
            self.update_particle_list()
        except ValueError:
            print("Ошибка: введите корректные значения.")

    def clear_particles(self):
        self.particles = []
        self.update_particle_list()
        self.canvas.figure.clear()
        self.canvas.draw()

    def update_particle_list(self):
        self.particle_list.clear()
        for i, p in enumerate(self.particles):
            self.particle_list.addItem(f"{i+1}: {str(p)}")

    def run_simulation(self):
        if not self.particles:
            return
        try:
            self.constants["G"] = float(self.g_input.text())
            self.constants["k"] = float(self.k_input.text())
            self.constants["tneeded"] = float(self.t_input.text())
            self.constants["max_points"] = self.max_points_input.value()
            self.constants["use_point_limits"] = self.use_limits_check.isChecked()
            self.constants["grid_size_x"] = self.grid_size_x_input.value()
            self.constants["grid_size_y"] = self.grid_size_y_input.value()
        except ValueError:
            print("Ошибка: проверьте значения G, k и времени симуляции.")
            return

        # Update max_points for all particles
        max_points = self.constants["max_points"]
        for p in self.particles:
            p.max_points = max_points

        self.save_settings()
        self.is_paused = False
        h = self.particles[0].dt
        steps = int(self.constants["tneeded"] / h) - 2

        # Store the current visualization type
        viz_type = self.viz_type_combo.currentText()
        stop_after_viz = self.stop_after_viz_check.isChecked()

        # Проверяем, нужно ли останавливать итерации после визуализации
        should_stop_after_viz = (stop_after_viz and
                                viz_type in ["Тепловая карта плотности",
                                             "Гистограмма по оси X",
                                             "Гистограмма по оси Y",
                                             "График энергии электрического взаимодействия",
                                             "График энергии гравитационного взаимодействия",
                                             "График энергии электрического взаимодействия (приближение)",
                                             "График энергии гравитационного взаимодействия (приближение)"])

        # Real-time simulation mode
        if self.real_time_radio.isChecked():
            self.update_period = self.periodicity_spin.value()
            for step in range(steps):
                if self.is_paused:
                    continue
                self.update_simulation_step()

                # Проверяем, нужно ли обновить визуализацию
                if step % self.update_period == 0:
                    self.canvas.figure.clear()

                    # Use the stored viz_type instead of getting it again
                    if viz_type == "Линии траекторий":
                        self.draw_trajectory_lines()
                    elif viz_type == "Тепловая карта плотности":
                        self.draw_density_heatmap()
                    elif viz_type == "Гистограмма по оси X":
                        self.draw_x_histogram()
                    elif viz_type == "Гистограмма по оси Y":
                        self.draw_y_histogram()
                    elif viz_type == "График энергии электрического взаимодействия":
                        self.draw_electric_energy_plot()
                    elif viz_type == "График энергии гравитационного взаимодействия":
                        self.draw_G_energy_plot()
                    elif viz_type == "График энергии электрического взаимодействия (приближение)":
                        self.draw_electric_diff_energy_plot()
                    elif viz_type == "График энергии гравитационного взаимодействия (приближение)":
                        self.draw_G_diff_energy_plot()

                    self.canvas.draw()
                    self.canvas.flush_events()
                    QApplication.processEvents()

                    # Если нужно остановить итерации после визуализации
                    if should_stop_after_viz and step > 0:
                        break
        else:
            # Default simulation mode (not real-time)
            # Если выбрана визуализация, которая требует остановки после первой итерации
            if should_stop_after_viz:
                # Выполняем только одну итерацию
                self.update_simulation_step()
            else:
                # Выполняем все итерации
                for _ in range(steps):
                    self.update_simulation_step()

            self.canvas.figure.clear()

            if viz_type == "Линии траекторий":
                self.draw_trajectory_lines()
            elif viz_type == "Тепловая карта плотности":
                self.draw_density_heatmap()
            elif viz_type == "Гистограмма по оси X":
                self.draw_x_histogram()
            elif viz_type == "Гистограмма по оси Y":
                self.draw_y_histogram()
            elif viz_type == "График энергии электрического взаимодействия":
                self.draw_electric_energy_plot()
            elif viz_type == "График энергии гравитационного взаимодействия":
                self.draw_G_energy_plot()
            elif viz_type == "График энергии электрического взаимодействия (приближение)":
                self.draw_electric_diff_energy_plot()
            elif viz_type == "График энергии гравитационного взаимодействия (приближение)":
                self.draw_G_diff_energy_plot()
            self.canvas.draw()

        # After the simulation completes, update the real-time calculations
        self.calculate_real_times()

    def compute_energy_el(self,t):
        kinetic = 0
        potential = 0

        for p in self.particles:
            vx=p.vx_history[t]
            vy=p.vy_history[t]
            kinetic += 0.5 * p.mass * (vx**2 + vy**2)

        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1, p2 = self.particles[i], self.particles[j]
                dx = p1.x_mass[t] - p2.x_mass[t]
                dy = p1.y_mass[t] - p2.y_mass[t]
                R = np.sqrt(dx**2 + dy**2)
                potential += self.constants["k"] * p1.charge * p2.charge / R
        return kinetic, potential, kinetic + potential

    def compute_energy_G(self,t):
        kinetic = 0
        potential = 0

        for p in self.particles:
            vx=p.vx_history[t]
            vy=p.vy_history[t]
            kinetic += 0.5 * p.mass * (vx**2 + vy**2)
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1, p2 = self.particles[i], self.particles[j]

                dx = p1.x_mass[t] - p2.x_mass[t]
                dy = p1.y_mass[t] - p2.y_mass[t]
                R = np.sqrt(dx**2 + dy**2)
                potential -= self.constants["G"] * p1.mass * p2.mass / R
        return kinetic, potential, kinetic + potential

    def draw_electric_energy_plot(self):
        K_list = []
        P_list = []
        E_list = []
        for t in range(1,len(self.particles[0].x_mass) - 1):
            K, P, E = self.compute_energy_el(t)
            K_list.append(K)
            P_list.append(P)
            E_list.append(E)
        ax = self.canvas.figure.add_subplot(111)
        ax.plot(K_list, label='Кинетическая энергия')
        ax.plot(P_list, label='Потенциальная энергия')
        ax.plot(E_list, label='Полная энергия')
        ax.legend()
        ax.grid(True)
        ax.set_xlabel("Время")
        ax.set_ylabel("Энергия")
        ax.set_title("Изменение энергии во времени")
    def draw_electric_diff_energy_plot(self):
        K_list = []
        P_list = []
        E_list = []
        for t in range(1,len(self.particles[0].x_mass) - 1):
            K, P, E = self.compute_energy_el(t)
            K_list.append(K)
            P_list.append(P)
            E_list.append(E)
        ax = self.canvas.figure.add_subplot(111)
        try:
            target_energy = float(self.target_energy_input.text())
        except ValueError:
            target_energy= -1.0
        #target_energy= -1.0
        diff=[]
        for i in range(len(E_list)):
            diff.append(E_list[i]-target_energy)
        ax.plot(np.arange(len(diff)) *self.particles[0].dt, diff)
        ax.axhline(y=0, color='r', linestyle='-')
        ax.grid(True)
        ax.set_xlabel("Время")
        ax.set_ylabel("Энергия")
        ax.set_title("Разность энергии во времени")
    def draw_G_energy_plot(self):
        K_list = []
        P_list = []
        E_list = []
        for t in range(1,len(self.particles[0].x_mass) - 1):
            K, P, E = self.compute_energy_G(t)
            K_list.append(K)
            P_list.append(P)
            E_list.append(E)
        ax = self.canvas.figure.add_subplot(111)
        ax.plot(K_list, label='Кинетическая энергия')
        ax.plot(P_list, label='Потенциальная энергия')
        ax.plot(E_list, label='Полная энергия')
        ax.legend()
        ax.grid(True)
        ax.set_xlabel("Время")
        ax.set_ylabel("Энергия")
        ax.set_title("Изменение энергии во времени")
    def draw_G_diff_energy_plot(self):
        K_list = []
        P_list = []
        E_list = []
        for t in range(1,len(self.particles[0].x_mass) - 1):
            K, P, E = self.compute_energy_G(t)
            K_list.append(K)
            P_list.append(P)
            E_list.append(E)
        ax = self.canvas.figure.add_subplot(111)
        try:
            target_energy = float(self.target_energy_input.text())
        except ValueError:
            target_energy= -1.0
        #target_energy= -1.0
        diff=[]
        for i in range(len(E_list)):
            diff.append(E_list[i]-target_energy)
        ax.plot(np.arange(len(diff)) *self.particles[0].dt, diff)
        ax.axhline(y=0, color='r', linestyle='-')
        ax.grid(True)
        ax.set_xlabel("Время")
        ax.set_ylabel("Энергия")
        ax.set_title("Разность энергии во времени")

    def draw_trajectory_lines(self):
        ax = self.canvas.figure.add_subplot(111)

        # Отрисовка траекторий с улучшенными метками для легенды
        for i, p in enumerate(self.particles):
            particle_num = i + 1  # Нумерация с 1
            label = f"ч{particle_num}: Q={p.charge}, m={p.mass}"
            ax.plot(p.x_mass, p.y_mass, color=p.color, label=label)

        # Улучшенная легенда - закреплена в правом верхнем углу с полупрозрачным фоном
        legend = ax.legend(
            loc='upper right',     # Положение в правом верхнем углу
            framealpha=0.3,        # Полупрозрачный фон (30% непрозрачности)
            fancybox=True,         # Скругленные углы
            shadow=False,          # Без тени
            fontsize='small'       # Небольшой размер шрифта
        )

        # Дополнительные настройки для стабильности легенды
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Траектории частиц')
        ax.grid(True)

    def draw_density_heatmap(self):
        if not self.particles or len(self.particles) < 1:
            return

        # Get grid sizes from settings
        gridsizex = self.constants["grid_size_x"]
        gridsizey = self.constants["grid_size_y"]

        # Find bounds for the grid
        all_x = []
        all_y = []
        for p in self.particles:
            all_x.extend(p.x_mass)
            all_y.extend(p.y_mass)

        if not all_x or not all_y:
            return

        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)

        # Add a small margin
        margin_x = (x_max - x_min) * 00.05
        margin_y = (y_max - y_min) * 0.05
        x_min -= margin_x
        x_max += margin_x
        y_min -= margin_y
        y_max += margin_y

        # Create a grid for counting particle positions
        intersection_counts = np.zeros((gridsizey, gridsizex))

        # Helper function to convert coordinates to grid indices
        def get_grid_indices(x, y, x_min, x_max, y_min, y_max, gridsizex, gridsizey):
            i = int((x - x_min) / (x_max - x_min) * (gridsizex - 1))
            j = int((y - y_min) / (y_max - y_min) * (gridsizey - 1))
            # Ensure indices are within bounds
            i = max(0, min(i, gridsizex - 1))
            j = max(0, min(j, gridsizey - 1))
            return i, j

        # Count particle positions on the grid
        # Focus on the first particle (typically the electron)
        if len(self.particles) > 0:
            for x, y in zip(self.particles[0].x_mass, self.particles[0].y_mass):
                if x_min <= x < x_max and y_min <= y < y_max:
                    i, j = get_grid_indices(x, y, x_min, x_max, y_min, y_max, gridsizex, gridsizey)
                    intersection_counts[j, i] += 1

        # Normalize the counts
        total_count = np.sum(intersection_counts)
        if total_count > 0:
            normalized_counts = intersection_counts / total_count
        else:
            normalized_counts = intersection_counts

        # Plot the heatmap
        ax = self.canvas.figure.add_subplot(111)
        im = ax.imshow(normalized_counts, extent=(x_min, x_max, y_min, y_max),
                      origin='lower', cmap='magma', aspect='auto')

        # Add colorbar and labels
        plt.colorbar(im, ax=ax, label='Вероятность')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Тепловая карта плотности частиц (частица 1)')

    def draw_x_histogram(self):
        """Draw histogram of particle positions along X-axis"""
        if not self.particles or len(self.particles) < 1:
            return

        # Get grid size from settings
        num_bins = self.constants["grid_size_x"]

        # Find bounds for the histogram
        all_x = []
        for p in self.particles:
            all_x.extend(p.x_mass)

        if not all_x:
            return

        x_min, x_max = min(all_x), max(all_x)

        # Add a small margin
        margin_x = (x_max - x_min) * 0.05
        x_min -= margin_x
        x_max += margin_x

        # Create histogram for the first particle (typically the electron)
        if len(self.particles) > 0:
            hist_counts, bin_edges = np.histogram(
                self.particles[0].x_mass,
                bins=num_bins,
                range=(x_min, x_max)
            )

            # Normalize the counts
            total_count = np.sum(hist_counts)
            if total_count > 0:
                hist_counts = hist_counts / total_count  # Normalize to get probabilities

            # Plot the histogram
            ax = self.canvas.figure.add_subplot(111)
            ax.bar(
                bin_edges[:-1],
                hist_counts,
                width=(x_max - x_min) / num_bins,
                color='black',
                alpha=0.7
            )

            # Add labels and grid
            ax.set_xlabel('X')
            ax.set_ylabel('Нормализованная вероятность' if total_count > 0 else 'Количество')
            ax.set_title('Гистограмма положений по оси X')
            ax.grid(True)

    def draw_y_histogram(self):
        """Draw histogram of particle positions along Y-axis"""
        if not self.particles or len(self.particles) < 1:
            return

        # Get grid size from settings
        num_bins = self.constants["grid_size_y"]

        # Find bounds for the histogram
        all_y = []
        for p in self.particles:
            all_y.extend(p.y_mass)

        if not all_y:
            return

        y_min, y_max = min(all_y), max(all_y)

        # Add a small margin
        margin_y = (y_max - y_min) * 0.05
        y_min -= margin_y
        y_max += margin_y

        # Create histogram for the first particle (typically the electron)
        if len(self.particles) > 0:
            hist_counts, bin_edges = np.histogram(
                self.particles[0].y_mass,
                bins=num_bins,
                range=(y_min, y_max)
            )

            # Normalize the counts
            total_count = np.sum(hist_counts)
            if total_count > 0:
                hist_counts = hist_counts / total_count  # Normalize to get probabilities

            # Plot the histogram
            ax = self.canvas.figure.add_subplot(111)
            ax.bar(
                bin_edges[:-1],
                hist_counts,
                width=(y_max - y_min) / num_bins,
                color='black',
                alpha=0.7
            )

            # Add labels and grid
            ax.set_xlabel('Y')
            ax.set_ylabel('Нормализованная вероятность' if total_count > 0 else 'Количество')
            ax.set_title('Гистограмма положений по оси Y')
            ax.grid(True)

    def compute_accelerations(self):
        # Reset all accelerations
        for p in self.particles:
            p.ax = 0
            p.ay = 0

        # Electric interactions
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                dx = p1.x_mass[-1] - p2.x_mass[-1]
                dy = p1.y_mass[-1] - p2.y_mass[-1]
                R = np.sqrt(dx * dx + dy * dy)
                if R > 0:
                    fx = self.constants["k"] * p1.charge * p2.charge * dx / (R**3)
                    fy = self.constants["k"] * p1.charge * p2.charge * dy / (R**3)
                else:
                    fx = fy = 0
                if p1.is_moving_ch:
                    p1.ax += fx / p1.mass
                    p1.ay += fy / p1.mass
                if p2.is_moving_ch:
                    p2.ax -= fx / p2.mass
                    p2.ay -= fy / p2.mass

        # Gravitational interactions
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                dx = p1.x_mass[-1] - p2.x_mass[-1]
                dy = p1.y_mass[-1] - p2.y_mass[-1]
                R = np.sqrt(dx * dx + dy * dy)
                if R > 0:
                    fx = -self.constants["G"] * p1.mass * p2.mass * dx / (R**3)
                    fy = -self.constants["G"] * p1.mass * p2.mass * dy / (R**3)
                else:
                    fx = fy = 0
                if p1.is_moving_m:
                    p1.ax += fx / p1.mass
                    p1.ay += fy / p1.mass
                if p2.is_moving_m:
                    p2.ax -= fx / p2.mass
                    p2.ay -= fy / p2.mass

    def verlet_step(self):
        h = self.particles[0].dt

        # Reset all accelerations
        for p in self.particles:
            p.ax = 0
            p.ay = 0

        # Electric interactions
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                dx = p1.x_mass[-1] - p2.x_mass[-1]
                dy = p1.y_mass[-1] - p2.y_mass[-1]
                R = np.sqrt(dx * dx + dy * dy)
                if R > 0:
                    fx = self.constants["k"] * p1.charge * p2.charge * dx / (R**3)
                    fy = self.constants["k"] * p1.charge * p2.charge * dy / (R**3)
                else:
                    fx = fy = 0
                if p1.is_moving_ch:
                    p1.ax += fx / p1.mass
                    p1.ay += fy / p1.mass
                if p2.is_moving_ch:
                    p2.ax -= fx / p2.mass
                    p2.ay -= fy / p2.mass

        # Gravitational interactions
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                dx = p1.x_mass[-1] - p2.x_mass[-1]
                dy = p1.y_mass[-1] - p2.y_mass[-1]
                R = np.sqrt(dx * dx + dy * dy)
                if R > 0:
                    fx = -self.constants["G"] * p1.mass * p2.mass * dx / (R**3)
                    fy = -self.constants["G"] * p1.mass * p2.mass * dy / (R**3)
                else:
                    fx = fy = 0
                if p1.is_moving_m:
                    p1.ax += fx / p1.mass
                    p1.ay += fy / p1.mass
                if p2.is_moving_m:
                    p2.ax -= fx / p2.mass
                    p2.ay -= fy / p2.mass

        # Verlet integration step
        for p in self.particles:
            if p.is_moving_ch or p.is_moving_m:
                new_x = 2 * p.x_mass[-1] - p.x_mass[-2] + h * h * p.ax
                new_y = 2 * p.y_mass[-1] - p.y_mass[-2] + h * h * p.ay
                p.vx=(new_x - p.x_mass[-1]) / h
                p.vy=(new_y - p.y_mass[-1]) / h
                p.add_point(new_x, new_y, self.constants["use_point_limits"])
                p.add_v(p.vx, p.vy)
            else:
                p.vx = 0
                p.vy = 0
                p.add_point(p.x_mass[-1], p.y_mass[-1], self.constants["use_point_limits"])
                p.add_v(p.vx,p.vy)

    def update_simulation_step(self):
        if self.verlet_radio.isChecked():
            self.verlet_step()
        elif self.leapfrog_radio.isChecked():
            self.leapfrog_step()
        elif self.rk4_radio.isChecked():
            self.rk4_step()
        else:
            self.bulirsch_stoer_step()

    def bulirsch_stoer_step(self):
        """Implement Bulirsch-Stoer integration method for particle simulation"""
        import numpy as np

        # Get time step from first particle
        h = self.particles[0].dt

        # Initialize state vector [x1,y1,x2,y2,...,vx1,vy1,vx2,vy2,...]
        n = len(self.particles)
        state = np.zeros(n * 4)

        # Fill state vector with current particle states
        for i, p in enumerate(self.particles):
            state[i*2] = p.x_mass[-1]      # x position
            state[i*2+1] = p.y_mass[-1]    # y position
            state[n*2+i*2] = p.vx          # x velocity
            state[n*2+i*2+1] = p.vy        # y velocity

        # Perform one Bulirsch-Stoer step
        new_state = self._bulirsch_stoer_integrator(state, h)

        # Update particles with new state
        for i, p in enumerate(self.particles):
            if p.is_moving_ch or p.is_moving_m:
                # Update position
                new_x = new_state[i*2]
                new_y = new_state[i*2+1]
                p.add_point(new_x, new_y, self.constants["use_point_limits"])
                # Update velocity
                p.vx = new_state[n*2+i*2]
                p.vy = new_state[n*2+i*2+1]
                p.add_v(p.vx,p.vy)
            else:
                # For non-moving particles, just duplicate the last position
                p.add_point(p.x_mass[-1], p.y_mass[-1], self.constants["use_point_limits"])
                p.add_v(p.vx,p.vy)

    def _compute_accelerations_for_bs(self, particles_state):
        """Compute accelerations for all particles based on their current state"""
        n = len(particles_state) // 4
        accelerations = np.zeros(n * 2)

        # Extract positions
        positions = np.array(particles_state[:n*2]).reshape(n, 2)

        # Compute forces and accelerations
        for i in range(n):
            for j in range(i + 1, n):
                p1 = self.particles[i]
                p2 = self.particles[j]

                dx = positions[i, 0] - positions[j, 0]
                dy = positions[i, 1] - positions[j, 1]
                R = np.sqrt(dx**2 + dy**2)

                if R > 0:
                    # Electric force
                    fx = self.constants["k"] * p1.charge * p2.charge * dx / R**3
                    fy = self.constants["k"] * p1.charge * p2.charge * dy / R**3

                    # Apply electric forces based on whether particles can move
                    if p1.is_moving_ch:
                        accelerations[i*2] += fx / p1.mass
                        accelerations[i*2+1] += fy / p1.mass
                    if p2.is_moving_ch:
                        accelerations[j*2] -= fx / p2.mass
                        accelerations[j*2+1] -= fy / p2.mass

                    # Gravitational force
                    fx = -self.constants["G"] * p1.mass * p2.mass * dx / R**3
                    fy = -self.constants["G"] * p1.mass * p2.mass * dy / R**3

                    # Apply gravitational forces based on whether particles can move
                    if p1.is_moving_m:
                        accelerations[i*2] += fx / p1.mass
                        accelerations[i*2+1] += fy / p1.mass
                    if p2.is_moving_m:
                        accelerations[j*2] -= fx / p2.mass
                        accelerations[j*2+1] -= fy / p2.mass

        return accelerations

    def _system_derivatives(self, state):
        """Compute derivatives for the entire system state [x1,y1,x2,y2,...,vx1,vy1,vx2,vy2,...]"""
        n = len(state) // 4
        derivatives = np.zeros_like(state)

        # Position derivatives = velocities
        derivatives[:n*2] = state[n*2:]

        # Velocity derivatives = accelerations
        derivatives[n*2:] = self._compute_accelerations_for_bs(state)

        return derivatives

    def _modified_midpoint_step(self, state, dt, n_substeps):
        """Modified midpoint method for a single step with n_substeps"""
        h = dt / n_substeps

        # Initialize
        y = np.copy(state)
        y_next = np.copy(state)
        d = np.copy(state)

        # First substep
        d += h * self._system_derivatives(y)
        y_next = d

        # Middle substeps
        for i in range(1, n_substeps):
            d = y + 2 * h * self._system_derivatives(y_next)
            y, y_next = y_next, d

        # Final substep
        return 0.5 * (y_next + y + h * self._system_derivatives(y_next))

    def _bulirsch_stoer_integrator(self, state, dt, eps=1e-8):
        """Perform one Bulirsch-Stoer step with adaptive sequence of substeps"""
        # Sequence of substep counts
        n_seq = [2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96]
        results = []
        errors = []

        # Try different numbers of substeps
        for n in n_seq:
            result = self._modified_midpoint_step(state, dt, n)
            results.append(result)

            # Check for convergence after we have at least 3 approximations
            if len(results) >= 3:
                # Use polynomial extrapolation to estimate the error
                error = np.max(np.abs(results[-1] - results[-2]))
                errors.append(error)

                # If error is small enough, return the extrapolated result
                if error < eps:
                    return results[-1]

        # If we didn0t converge, return the best approximation
        return results[-1]

    def add_default_particles(self):
        max_points = self.constants["max_points"]
        self.particles.append(Particle(0, 0, -1, 1, 1, 45, 0.0001, True, False, 'red', max_points))
        self.particles.append(Particle(-1, 0, 1, 1836, 0, 0, 0.0001, False, False, 'green', max_points))
        self.particles.append(Particle(1, 0, 1, 1836, 0, 0, 0.0001, False, False, 'blue', max_points))
        self.update_particle_list()

    def save_particles_to_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить частицы", "", "JSON файлы (*.json)")
        if filename:
            data = [p.to_dict() for p in self.particles]
            with open(filename, "w") as f:
                json.dump(data, f)

    def load_particles_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Открыть список частиц", "", "JSON файлы (*.json)")
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
            self.particles = [Particle.from_dict(d) for d in data]
            self.update_particle_list()

    def save_settings(self):
        settings = {
            "G": self.constants["G"],
            "k": self.constants["k"],
            "tneeded": self.constants["tneeded"],
            "use_point_limits": self.constants["use_point_limits"]
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            self.constants.update(settings)

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def calculate_real_times(self):
        try:
            # Get values from input fields
            real_mass1 = float(self.real_mass1_input.text())
            real_mass2 = float(self.real_mass2_input.text())
            real_distance = float(self.real_distance_input.text())
            real_charge1 = float(self.real_charge1_input.text())
            real_charge2 = float(self.real_charge2_input.text())

            # Constants in SI units
            k_real = 9e9  # Coulomb constant (N·m²/C²)
            G_real = 6.67430e-11  # Gravitational constant (m³/kg·s²)

            # Calculate electrostatic time using the formula: sqrt(m*r/(k*|Q|*|q|))
            electrostatic_time = math.sqrt(real_mass1 * real_distance**3 / (k_real * abs(real_charge1) * abs(real_charge2)))

            # Calculate gravitational time using the formula: sqrt(r³/(G*(m1+m2)))
            gravitational_time = math.sqrt(real_distance**3 / (G_real * (real_mass2)))#real_mass1+

            # Display the results
            self.electrostatic_time_output.setText(f"{electrostatic_time:.2e} с")
            self.gravitational_time_output.setText(f"{gravitational_time:.2e} с")

        except ValueError as e:
            self.electrostatic_time_output.setText(f"Error: {str(e)}")
            self.gravitational_time_output.setText(f"Error: {str(e)}")

    def create_menu_bar(self):
        menubar = self.menuBar()

        # Help menu
        help_menu = menubar.addMenu("Справка")

        # About action
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # User Guide action
        user_guide_action = QAction("Руководство пользователя", self)
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)

    def show_about(self):
        try:
            with open(ABOUT_FILE, "r", encoding="utf-8") as file:
                about_content = file.read()
        except FileNotFoundError:
            about_content = "<h1>Руководство пользователя</h1><p>Файл руководства не найден. Пожалуйста, создайте файл 'user_guide.html'.</p>"

        dialog = HelpDialog("О симуляторе частиц", about_content, self)
        dialog.exec_()

    def show_user_guide(self):
        CHM_FILE = "particle_sim.chm"

        if os.path.exists(CHM_FILE):
            try:
                # Open CHM file using the default Windows CHM viewer
                subprocess.Popen(f'hh.exe "{os.path.abspath(CHM_FILE)}"', shell=True)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл справки: {str(e)}")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Файл не найден", f"Файл справки '{CHM_FILE}' не найден.")


    def rk4_step(self):
        h = self.particles[0].dt

        # Save initial states
        posx0 = [p.x_mass[-1] for p in self.particles]
        posy0 = [p.y_mass[-1] for p in self.particles]
        vx0 = [p.vx for p in self.particles]
        vy0 = [p.vy for p in self.particles]

        # k1
        self.compute_accelerations()
        k1_vx = [p.ax for p in self.particles]
        k1_vy = [p.ay for p in self.particles]
        k1_x = [p.vx for p in self.particles]
        k1_y = [p.vy for p in self.particles]

        # k2
        for i, p in enumerate(self.particles):
            if p.is_moving_ch or p.is_moving_m:
                p.x_mass[-1] = posx0[i] + 0.5 * h * k1_x[i]
                p.y_mass[-1] = posy0[i] + 0.5 * h * k1_y[i]
                p.vx = vx0[i] + 0.5 * h * k1_vx[i]
                p.vy = vy0[i] + 0.5 * h * k1_vy[i]

        self.compute_accelerations()
        k2_vx = [p.ax for p in self.particles]
        k2_vy = [p.ay for p in self.particles]
        k2_x = [p.vx for p in self.particles]
        k2_y = [p.vy for p in self.particles]

        # k3
        for i, p in enumerate(self.particles):
            if p.is_moving_ch or p.is_moving_m:
                p.x_mass[-1] = posx0[i] + 0.5 * h * k2_x[i]
                p.y_mass[-1] = posy0[i] + 0.5 * h * k2_y[i]
                p.vx = vx0[i] + 0.5 * h * k2_vx[i]
                p.vy = vy0[i] + 0.5 * h * k2_vy[i]

        self.compute_accelerations()
        k3_vx = [p.ax for p in self.particles]
        k3_vy = [p.ay for p in self.particles]
        k3_x = [p.vx for p in self.particles]
        k3_y = [p.vy for p in self.particles]

        # k4
        for i, p in enumerate(self.particles):
            if p.is_moving_ch or p.is_moving_m:
                p.x_mass[-1] = posx0[i] + h * k3_x[i]
                p.y_mass[-1] = posy0[i] + h * k3_y[i]
                p.vx = vx0[i] + h * k3_vx[i]
                p.vy = vy0[i] + h * k3_vy[i]

        self.compute_accelerations()
        k4_vx = [p.ax for p in self.particles]
        k4_vy = [p.ay for p in self.particles]
        k4_x = [p.vx for p in self.particles]
        k4_y = [p.vy for p in self.particles]

        # Update states
        for i, p in enumerate(self.particles):
            if p.is_moving_ch or p.is_moving_m:
                new_vx = vx0[i] + (h/6)*(k1_vx[i] + 2*k2_vx[i] + 2*k3_vx[i] + k4_vx[i])
                new_vy = vy0[i] + (h/6)*(k1_vy[i] + 2*k2_vy[i] + 2*k3_vy[i] + k4_vy[i])
                new_x = posx0[i] + (h/6)*(k1_x[i] + 2*k2_x[i] + 2*k3_x[i] + k4_x[i])
                new_y = posy0[i] + (h/6)*(k1_y[i] + 2*k2_y[i] + 2*k3_y[i] + k4_y[i])

                p.vx = new_vx
                p.vy = new_vy
                p.add_v(p.vx,p.vy)
                # Restore original position before adding the new point
                p.x_mass[-1] = posx0[i]
                p.y_mass[-1] = posy0[i]
                p.add_point(new_x, new_y, self.constants["use_point_limits"])
            else:
                p.add_point(p.x_mass[-1], p.y_mass[-1], self.constants["use_point_limits"])
                p.add_v(p.vx,p.vy)

    def reset_simulation(self):
        # Reset each particle to its initial state
        for p in self.particles:
            # Keep only the first two points (initial position and first step)
            if len(p.x_mass) > 2:
                p.x_mass = p.x_mass_init[:2]
                p.y_mass = p.y_mass_init[:2]

            # Reset velocity to initial values based on angle and velocity
            rad_angle = math.radians(p.angle)
            p.vx = p.velocity * np.cos(rad_angle)
            p.vy = p.velocity * np.sin(rad_angle)
            p.vx_history=[0,p.vx]
            p.vy_history=[0,p.vy]
            # Reset acceleration
            p.ax = 0
            p.ay = 0

        # Clear the canvas
        self.canvas.figure.clear()
        self.canvas.draw()

        # Update the particle list to show reset positions
        self.update_particle_list()

    def leapfrog_step(self):
            h = self.particles[0].dt

            # Save initial states
            posx0 = [p.x_mass[-1] for p in self.particles]
            posy0 = [p.y_mass[-1] for p in self.particles]
            vx0 = [p.vx for p in self.particles]
            vy0 = [p.vy for p in self.particles]

            # First half-step for velocities (previous step)
            for i, p in enumerate(self.particles):
                if p.is_moving_ch or p.is_moving_m:
                    p.vx += 0.5 * h * p.ax
                    p.vy += 0.5 * h * p.ay

            # Update positions for full step
            for i, p in enumerate(self.particles):
                if p.is_moving_ch or p.is_moving_m:
                    new_x = posx0[i] + h * p.vx
                    new_y = posy0[i] + h * p.vy
                    p.add_point(new_x, new_y, self.constants["use_point_limits"])

                else:
                    # For non-moving particles, just duplicate the last position
                    p.add_point(p.x_mass[-1], p.y_mass[-1], self.constants["use_point_limits"])
                    # p.add_v((vx0[i]+p.vx)/2,(vy0[i]+p.vy)/2)

            # Recalculate accelerations
            self.compute_accelerations()

            # Second half-step for velocities (based on new accelerations)
            for i, p in enumerate(self.particles):
                if p.is_moving_ch or p.is_moving_m:
                    p.vx += 0.5 * h * p.ax
                    p.vy += 0.5 * h * p.ay
                p.add_v(p.vx,p.vy)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParticleSimulator()
    window.show()
    sys.exit(app.exec_())
