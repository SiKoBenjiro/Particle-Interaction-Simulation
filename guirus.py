import numpy as np
import matplotlib.pyplot as plt
import math
from tkinter import *
from tkinter import messagebox

class Particle:
    def __init__(self, posx, posy, charge, mass, v, angle, dt, is_moving_ch, is_moving_m):
        self.charge = charge
        self.mass = mass
        self.is_moving_ch = is_moving_ch
        self.is_moving_m = is_moving_m
        self.x_mass = [posx, posx + v * np.cos(math.radians(angle)) * dt]
        self.y_mass = [posy, posy + v * np.sin(math.radians(angle)) * dt]
        self.ax = 0
        self.ay = 0
        self.axm = 0
        self.aym = 0

def charge_interact_step_a(part1, part2):
    r = np.sqrt((part1.x_mass[-1] - part2.x_mass[-1]) ** 2 + (part1.y_mass[-1] - part2.y_mass[-1]) ** 2)
    if r > 0:
        fx = k * part1.charge * part2.charge * (part1.x_mass[-1] - part2.x_mass[-1]) / r ** 3
        fy = k * part1.charge * part2.charge * (part1.y_mass[-1] - part2.y_mass[-1]) / r ** 3
    else:
        fx = 0
        fy = 0
    if part1.is_moving_ch:
        part1.ax += fx / part1.mass
        part1.ay += fy / part1.mass
    if part2.is_moving_ch:
        part2.ax += -fx / part2.mass
        part2.ay += -fy / part2.mass

def charge_interact_step_b(part):
    if part.is_moving_ch:
        part.x_mass.append(2 * part.x_mass[-1] - part.x_mass[-2] + h * h * part.ax)
        part.y_mass.append(2 * part.y_mass[-1] - part.y_mass[-2] + h * h * part.ay)
    part.ax = 0
    part.ay = 0

def center_interact_step_a(part1, part2):
    r = np.sqrt((part1.x_mass[-1] - part2.x_mass[-1]) ** 2 + (part1.y_mass[-1] - part2.y_mass[-1]) ** 2)
    if r > 0:
        fx = -G * part1.mass * part2.mass * (part1.x_mass[-1] - part2.x_mass[-1]) / r ** 3
        fy = -G * part1.mass * part2.mass * (part1.y_mass[-1] - part2.y_mass[-1]) / r ** 3
    else:
        fx = 0
        fy = 0
    if part1.is_moving_m:
        part1.axm += fx / part1.mass
        part1.aym += fy / part1.mass
    if part2.is_moving_m:
        part2.axm += -fx / part2.mass
        part2.aym += -fy / part2.mass

def center_interact_step_b(part):
    if part.is_moving_m:
        part.x_mass.append(2 * part.x_mass[-1] - part.x_mass[-2] + h * h * part.axm)
        part.y_mass.append(2 * part.y_mass[-1] - part.y_mass[-2] + h * h * part.aym)
    part.axm = 0
    part.aym = 0

def charge_interaction():
    for k in range(iterations.get()):
        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                charge_interact_step_a(particles[i], particles[j])
        for i in range(len(particles)):
            charge_interact_step_b(particles[i])

def center_interaction():
    for k in range(iterations.get()):
        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                center_interact_step_a(particles[i], particles[j])
        for i in range(len(particles)):
            center_interact_step_b(particles[i])

def add_particle():
    charge = float(charge_entry.get())
    mass = float(mass_entry.get())
    is_moving_ch = bool(charge_moving_var.get())
    is_moving_m = bool(mass_moving_var.get())
    posx = float(posx_entry.get())
    posy = float(posy_entry.get())
    v = float(velocity_entry.get())  # Добавлен ввод скорости
    angle = float(angle_entry.get())
    particles.append(Particle(posx, posy, charge, mass, v, angle, h, is_moving_ch, is_moving_m))
    update_particle_list()

def remove_particle():
    if particles_listbox.curselection():
        index = particles_listbox.curselection()[0]
        del particles[index]
        update_particle_list()

def clear_memory():
    global particles
    for particle in particles:
        particle.x_mass = [particle.x_mass[0], particle.x_mass[1]]
        particle.y_mass = [particle.y_mass[0], particle.y_mass[1]]
        particle.ax = 0
        particle.ay = 0
        particle.axm = 0
        particle.aym = 0
    update_particle_list()

def update_parameters():
    global G, k
    G = float(G_entry.get())
    k = float(k_entry.get())

def update_particle_list():
    particles_listbox.delete(0, END)
    for i, particle in enumerate(particles):
        coordinates = f"X={particle.x_mass[-1]:.2f}, Y={particle.y_mass[-1]:.2f}"
        properties = f"Charge={particle.charge}, Mass={particle.mass}, Moving Charge={particle.is_moving_ch}, Moving Mass={particle.is_moving_m}"
        particles_listbox.insert(END, f"Частица {i + 1}: {coordinates}, {properties}")

def run_simulation():
    charge_interaction()
    center_interaction()
    plot_simulation()

def plot_simulation():
    plt.figure(figsize=(8, 6))
    for particle in particles:
        plt.plot(particle.x_mass, particle.y_mass)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Симуляция взаимодействия частиц')
    plt.grid(True)
    plt.show()

def show_help():
    help_text = """
    Это программа симуляции взаимодействия частиц.

    Инструкции:
    1. Добавьте частицы, используя кнопку 'Добавить частицу'.
    2. Настройте свойства частиц, такие как заряд, масса, начальное положение, скорость и угол.
    3. Выберите возможность частицы двигаться в определённом взаимодействии
    Кулоновское - противоположности по заряду притягиваются
    Гравитационное - взаимодействуют массы
    4. Установите количество итераций для симуляции.
    5. Обновите физические константы (константа G и константа k), если это необходимо.
    6. Запустите симуляцию.
    Кнопка Обновить параметры сбрасывает количество итераций
    !!Важно: нужно указывать нужное взаимодействие для частиц
    В начальных условиях заряд в кулонах, масса в килограммах, расстояние (в теории) в метрах
    Для кулоновского взаимодействия рекомендуется поставить k=1.

    Также обраттите внимание, что для красивой картинки в графитационном взаимодействии нужно
    подобрать правильно начальную скорость и направление движения частицы.
    К примеру, для 2 частиц на расстоянии 2 друг от друга(Х1=-1,Х2=1,Y=0), при G=906.67*10**(-11)=9.0667е(-9), скорости направлены под 180 градусов друг к другу (одна ввурх, другая вниз), скорости 2.0425*10**(-3) через примерно 20 миллионов итераций частицы поменяются местами


    """
    #Примечание: После запуска симуляции координаты каждой частицы отображаются в списке частиц.
    messagebox.showinfo("Справка", help_text)

G = 1
k = 1
V = 1
PI = math.pi
alpha = 60  # Начальный угол в градусах
t_needed = 2000
h = 0.0001
particles = []

root = Tk()
root.title("Симуляция взаимодействия частиц")

# Создаем главное меню
menu_bar = Menu(root)
root.config(menu=menu_bar)

# Добавляем пункт меню "File" с подменю
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Справка", menu=file_menu)

# Добавляем пункт "Справка" в меню "File"
file_menu.add_command(label="Справка", command=show_help)

# Название программы
title_label = Label(root, text="Симуляция взаимодействия частиц", font=("Arial", 14, "bold"))
title_label.pack()

charge_label = Label(root, text="Заряд:")
charge_label.pack()
charge_entry = Entry(root)
charge_entry.pack()
charge_entry.insert(0, "-1")

mass_label = Label(root, text="Масса:")
mass_label.pack()
mass_entry = Entry(root)
mass_entry.pack()
mass_entry.insert(0, "1")

charge_moving_var = BooleanVar()
charge_moving_checkbox = Checkbutton(root, text="Кулоновское взаимодействие", variable=charge_moving_var)
charge_moving_checkbox.pack()

mass_moving_var = BooleanVar()
mass_moving_checkbox = Checkbutton(root, text="Гравитационное взаимодействие", variable=mass_moving_var)
mass_moving_checkbox.pack()

posx_label = Label(root, text="Начальная X позиция:")
posx_label.pack()
posx_entry = Entry(root)
posx_entry.pack()
posx_entry.insert(0, "0")

posy_label = Label(root, text="Начальная Y позиция:")
posy_label.pack()
posy_entry = Entry(root)
posy_entry.pack()
posy_entry.insert(0, "0")

velocity_label = Label(root, text="Начальная скорость:")  # Добавлено название для скорости
velocity_label.pack()
velocity_entry = Entry(root)
velocity_entry.pack()
velocity_entry.insert(0, "1")

angle_label = Label(root, text="Начальный угол (градусы):")  # Изменено название для указания градусов
angle_label.pack()
angle_entry = Entry(root)
angle_entry.pack()
angle_entry.insert(0, str(alpha))

iterations_label = Label(root, text="Количество итераций:")
iterations_label.pack()
iterations = IntVar()
iterations_entry = Entry(root, textvariable=iterations)
iterations_entry.pack()
iterations_entry.insert(0, "2000")



add_button = Button(root, text="Добавить частицу", command=add_particle)
add_button.pack()

remove_button = Button(root, text="Удалить выбранную частицу", command=remove_particle)
remove_button.pack()

clear_button = Button(root, text="Очистить память", command=clear_memory)  # Добавлена кнопка очистки
clear_button.pack()

G_label = Label(root, text="Константа G:")
G_label.pack()
G_entry = Entry(root)
G_entry.pack()
G_entry.insert(0, str(G))

k_label = Label(root, text="Константа k:")
k_label.pack()
k_entry = Entry(root)
k_entry.pack()
k_entry.insert(0, str(k))

update_button = Button(root, text="Обновить параметры", command=update_parameters)
update_button.pack()

particles_listbox = Listbox(root, width=50, height=10)
particles_listbox.pack()

simulation_button = Button(root, text="Запустить симуляцию", command=run_simulation)
simulation_button.pack()

root.mainloop()
