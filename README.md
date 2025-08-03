# Wheels On Motion (Windows Edition) 🎧🦽

**Wheels On Motion** is an artistic project that transforms movement data from wheelchair users into immersive soundscapes.  
The goal is to sonify the often invisible physical difficulties faced in everyday navigation through public and private spaces.

This Windows-based Python application uses geolocation and sensor data collected via a custom Android app (APK) to generate sound in real time or from recorded routes.

> **APK Source**: [Download APK here](https://github.com/zeligmax/Wheels_On_Motion_Android/blob/main/app-debug.apk)

---

## 🔊 What It Does

- Reads movement data from a `.txt` or `.csv` file exported by the mobile app:
  - **Latitude**, **Longitude**
  - **Altitude**
  - **Gyroscope X**, **Y**, **Z**
- Translates those numeric values into evolving audio signals.
- Highlights unstable paths, sharp turns, or sudden shifts through sound texture and pitch changes.

This creates an auditory landscape of physical motion, revealing terrain irregularities, vibration patterns, and directional stress — offering a new perspective on mobility and accessibility.

---

## 📦 Requirements

- Python 3.x  
- Works on **Windows OS**  
- Recommended libraries:
  - `pygame`
  - `numpy`
  - `simpleaudio`
  - `pandas`

Install them with:

```bash
pip install pygame numpy simpleaudio pandas
```bash

▶️ How to Run
Clone this repository:

bash
Copiar
Editar
git clone https://github.com/zeligmax/Wheels_On_Motion_Windows.git
cd Wheels_On_Motion_Windows
Launch one of the main scripts:

bash
Copiar
Editar
python 0Nice_mapa_sonoro1.py
Or:

bash
Copiar
Editar
python "mapa_sonoro0 copy4.py"
Select the data file when prompted or drag a .txt file with the recorded sensor data.

🗂 Project Structure
Copiar
Editar
Wheels_On_Motion_Windows/
├── 0Nice_mapa_sonoro1.py
├── mapa_sonoro0 copy4.py
├── sample_data/
│   └── example_track.txt
└── README.md
🎨 Artistic Purpose
This is not just a technical experiment — it's a form of digital storytelling.

The sonic interpretation makes tactile and spatial difficulties audible, giving a voice to the textures of the world that wheelchairs navigate daily.

It invites reflection on urban design, accessibility, and empathy.

🤝 Contributing
Contributions, collaborations, and sonic experiments are welcome.

Fork the repo

Create a feature branch: git checkout -b feature/your-idea

Submit a pull request

📄 License
This project is released under the MIT License.

Developed by Zeligmax – 2025
