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
    v = float(velocity_entry.get())  # Added velocity input
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
        particles_listbox.insert(END, f"Particle {i + 1}: {coordinates}, {properties}")

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
    plt.title('Particle Interaction Simulation')
    plt.grid(True)
    plt.show()

def show_help():
    help_text = """
    This is a particle interaction simulation program.

    Instructions:
    1. Add particles using the 'Add Particle' button.
    2. Configure particle properties such as charge, mass, initial position, velocity, and angle.
    3. Select the interaction type: Charge Interaction or Center Interaction.
    4. Set the number of iterations for the simulation.
    5. Update the physical constants (G constant and k constant) if needed.
    6. Run the simulation

    Note: The coordinates of each particle are displayed in the particle list after running the simulation.
    """
    messagebox.showinfo("Help", help_text)

G = 1
k = 1
V = 1
PI = math.pi
alpha = 60  # Initial angle in degrees
t_needed = 2000
h = 0.0001
particles = []

root = Tk()
root.title("Particle Interaction Simulation")

# Создаем главное меню
menu_bar = Menu(root)
root.config(menu=menu_bar)

# Добавляем пункт меню "File" с подменю
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="help", menu=file_menu)

# Добавляем пункт "Help" в меню "File"
file_menu.add_command(label="Help", command=show_help)

# Название программы
title_label = Label(root, text="Particle Interaction Simulation", font=("Arial", 14, "bold"))
title_label.pack()

charge_label = Label(root, text="Charge:")
charge_label.pack()
charge_entry = Entry(root)
charge_entry.pack()
charge_entry.insert(0, "-1")

mass_label = Label(root, text="Mass:")
mass_label.pack()
mass_entry = Entry(root)
mass_entry.pack()
mass_entry.insert(0, "1")

charge_moving_var = BooleanVar()
charge_moving_checkbox = Checkbutton(root, text="Moving Charge", variable=charge_moving_var)
charge_moving_checkbox.pack()

mass_moving_var = BooleanVar()
mass_moving_checkbox = Checkbutton(root, text="Moving Mass", variable=mass_moving_var)
mass_moving_checkbox.pack()

posx_label = Label(root, text="Initial X Position:")
posx_label.pack()
posx_entry = Entry(root)
posx_entry.pack()
posx_entry.insert(0, "0")

posy_label = Label(root, text="Initial Y Position:")
posy_label.pack()
posy_entry = Entry(root)
posy_entry.pack()
posy_entry.insert(0, "0")

velocity_label = Label(root, text="Initial Velocity:")  # Added velocity label
velocity_label.pack()
velocity_entry = Entry(root)
velocity_entry.pack()
velocity_entry.insert(0, "1")

angle_label = Label(root, text="Initial Angle (Degrees):")  # Changed label to mention degrees
angle_label.pack()
angle_entry = Entry(root)
angle_entry.pack()
angle_entry.insert(0, str(alpha))

iterations_label = Label(root, text="Number of Iterations:")
iterations_label.pack()
iterations = IntVar()
iterations_entry = Entry(root, textvariable=iterations)
iterations_entry.pack()
iterations_entry.insert(0, "2000")



add_button = Button(root, text="Add Particle", command=add_particle)
add_button.pack()

remove_button = Button(root, text="Remove Selected Particle", command=remove_particle)
remove_button.pack()

clear_button = Button(root, text="Clear Memory", command=clear_memory)  # Added clear button
clear_button.pack()

G_label = Label(root, text="G constant:")
G_label.pack()
G_entry = Entry(root)
G_entry.pack()
G_entry.insert(0, str(G))

k_label = Label(root, text="k constant:")
k_label.pack()
k_entry = Entry(root)
k_entry.pack()
k_entry.insert(0, str(k))

update_button = Button(root, text="Update Parameters", command=update_parameters)
update_button.pack()

particles_listbox = Listbox(root, width=50, height=10)
particles_listbox.pack()

simulation_button = Button(root, text="Run Simulation", command=run_simulation)
simulation_button.pack()

root.mainloop()
