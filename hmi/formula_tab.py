"""
Formula Tab - System Equations Display
=======================================

Modern tab showing the mathematical model equations with language support.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTextEdit, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class FormulaTab(QWidget):
    """Tab displaying system equations and model with bilingual support"""

    def __init__(self, parent=None, language='en'):
        super().__init__(parent)
        self.language = language
        self.setup_ui()

    def set_language(self, language: str):
        """Update language and refresh UI"""
        self.language = language
        self.setup_ui()

    def setup_ui(self):
        """Setup formula display UI"""
        # Clear existing layout
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title_text = {
            'en': "Mathematical Model",
            'uk': "Математична модель"
        }
        title = QLabel(title_text[self.language])
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1565c0; padding: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll area for equations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(25)

        # 1. Main Differential Equation
        content_layout.addWidget(self._create_card(
            self._get_text('main_title'),
            self._get_main_equation_html(),
            "#e3f2fd",
            "#1976d2"
        ))

        # 2. State Variables
        content_layout.addWidget(self._create_card(
            self._get_text('state_title'),
            self._get_state_variables_html(),
            "#fff3e0",
            "#f57c00"
        ))

        # 3. Target Temperature
        content_layout.addWidget(self._create_card(
            self._get_text('target_title'),
            self._get_target_temperature_html(),
            "#e8f5e9",
            "#388e3c"
        ))

        # 4. Transport Delay
        content_layout.addWidget(self._create_card(
            self._get_text('delay_title'),
            self._get_transport_delay_html(),
            "#fff9c4",
            "#f9a825"
        ))

        # 5. Water Temperature
        content_layout.addWidget(self._create_card(
            self._get_text('water_title'),
            self._get_water_temperature_html(),
            "#f3e5f5",
            "#7b1fa2"
        ))

        # 6. Parameters Table
        content_layout.addWidget(self._create_card(
            self._get_text('params_title'),
            self._get_parameters_table_html(),
            "#fafafa",
            "#455a64"
        ))

        # 7. Transfer Function
        content_layout.addWidget(self._create_card(
            self._get_text('transfer_title'),
            self._get_transfer_function_html(),
            "#fce4ec",
            "#c2185b"
        ))

        # 8. Old vs New Formula
        content_layout.addWidget(self._create_card(
            self._get_text('comparison_title'),
            self._get_formula_comparison_html(),
            "#fff8e1",
            "#f57f17"
        ))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_card(self, title: str, html: str, bg_color: str, accent_color: str) -> QFrame:
        """Create modern card-style equation display with shadow and gradient"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: none;
            }}
        """)

        # Add subtle shadow effect
        card.setGraphicsEffect(self._create_shadow_effect())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar with gradient
        title_bar = QLabel(title)
        title_bar.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_bar.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent_color},
                stop:1 {self._lighten_color(accent_color)}
            );
            color: white;
            padding: 20px 25px;
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        """)
        layout.addWidget(title_bar)

        # Content with better padding
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(html)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                border: none;
                padding: 25px;
                color: #212121;
                font-size: 15px;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }}
        """)

        text_edit.setMinimumHeight(200)
        layout.addWidget(text_edit)

        return card

    def _create_shadow_effect(self):
        """Create shadow effect for cards"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        return shadow

    def _lighten_color(self, color: str) -> str:
        """Lighten a hex color for gradient"""
        # Simple lightening - convert hex to RGB, increase brightness
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        # Lighten by adding 30 to each component (max 255)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text(self, key: str) -> str:
        """Get translated text"""
        texts = {
            'en': {
                'main_title': "Main Differential Equation",
                'state_title': "State Variables",
                'target_title': "Target Temperature",
                'delay_title': "Transport Delay",
                'water_title': "Water Temperature",
                'params_title': "System Parameters",
                'transfer_title': "Transfer Function",
                'comparison_title': "Why was the old formula unstable?"
            },
            'uk': {
                'main_title': "Основне диференціальне рівняння",
                'state_title': "Змінні стану",
                'target_title': "Цільова температура",
                'delay_title': "Транспортне запізнення",
                'water_title': "Температура води",
                'params_title': "Параметри системи",
                'transfer_title': "Передавальна функція",
                'comparison_title': "Чому стара формула була нестабільною?"
            }
        }
        return texts[self.language][key]

    def _get_main_equation_html(self) -> str:
        """Get main equation HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.4; color: #212121;'>
<div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin-bottom: 18px; border-left: 5px solid #1976d2;'>
<p style='margin: 0 0 15px 0;'><b style='color: #0d47a1; font-size: 18px;'>📐 Стандартна форма диференціального рівняння:</b></p>
<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);'>
<p style='text-align: center; margin: 0;'>
<span style='font-size: 20px; color: #1565c0; font-weight: 600; font-family: "Cambria Math", serif;'>
T₁·T₂·ÿ + (T₁+T₂)·ẏ + (y - y<sub>target</sub>) = 0
</span>
</p>
</div>
</div>

<div style='background: #f5f5f5; padding: 18px; border-radius: 10px; margin-bottom: 18px;'>
<p style='margin: 0 0 12px 0;'><b style='color: #424242; font-size: 17px;'>де цільова температура:</b></p>
<div style='background: white; padding: 16px; border-radius: 8px; border: 2px solid #e0e0e0;'>
<p style='text-align: center; margin: 0;'>
<span style='font-size: 18px; color: #1565c0; font-weight: 500; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u + K<sub>z</sub>·(T<sub>out</sub> - T<sub>amb,ref</sub>)
</span>
</p>
</div>
</div>

<div style='background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);'>
<p style='margin: 0 0 15px 0; color: white;'><b style='font-size: 18px;'>✨ Розв'язок для прискорення ÿ:</b></p>
<div style='background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px);'>
<p style='text-align: center; margin: 0;'>
<span style='color: white; font-size: 20px; font-weight: bold; font-family: "Cambria Math", serif; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·(y - y<sub>target</sub>)
</span>
</p>
</div>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.4; color: #212121;'>
<div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin-bottom: 18px; border-left: 5px solid #1976d2;'>
<p style='margin: 0 0 15px 0;'><b style='color: #0d47a1; font-size: 18px;'>📐 Standard Form of Differential Equation:</b></p>
<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);'>
<p style='text-align: center; margin: 0;'>
<span style='font-size: 20px; color: #1565c0; font-weight: 600; font-family: "Cambria Math", serif;'>
T₁·T₂·ÿ + (T₁+T₂)·ẏ + (y - y<sub>target</sub>) = 0
</span>
</p>
</div>
</div>

<div style='background: #f5f5f5; padding: 18px; border-radius: 10px; margin-bottom: 18px;'>
<p style='margin: 0 0 12px 0;'><b style='color: #424242; font-size: 17px;'>where target temperature is:</b></p>
<div style='background: white; padding: 16px; border-radius: 8px; border: 2px solid #e0e0e0;'>
<p style='text-align: center; margin: 0;'>
<span style='font-size: 18px; color: #1565c0; font-weight: 500; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u + K<sub>z</sub>·(T<sub>out</sub> - T<sub>amb,ref</sub>)
</span>
</p>
</div>
</div>

<div style='background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);'>
<p style='margin: 0 0 15px 0; color: white;'><b style='font-size: 18px;'>✨ Solution for acceleration ÿ:</b></p>
<div style='background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px);'>
<p style='text-align: center; margin: 0;'>
<span style='color: white; font-size: 20px; font-weight: bold; font-family: "Cambria Math", serif; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·(y - y<sub>target</sub>)
</span>
</p>
</div>
</div>
</div>
"""

    def _get_state_variables_html(self) -> str:
        """Get state variables HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<div style='background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
<p style='margin: 8px 0;'><b style='color: #e65100;'>x₁</b> <span style='color: #424242;'>= y (температура теплиці, °C)</span></p>
<p style='margin: 8px 0;'><b style='color: #e65100;'>x₂</b> <span style='color: #424242;'>= ẏ (швидкість зміни температури, °C/с)</span></p>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #e65100; font-size: 17px;'>Інтегрування методом Ейлера:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #f57c00;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
x₂<sub>new</sub> = x₂<sub>old</sub> + Δt · ÿ<br>
x₁<sub>new</sub> = x₁<sub>old</sub> + Δt · x₂<sub>old</sub>
</p>
</div>

<div style='background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px dashed #ff6f00;'>
<p style='margin: 0; color: #e65100; font-size: 15px;'>
<b>⚠️ ВАЖЛИВО:</b> x₁ оновлюється зі <b>СТАРИМ</b> значенням x₂!
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<div style='background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
<p style='margin: 8px 0;'><b style='color: #e65100;'>x₁</b> <span style='color: #424242;'>= y (greenhouse temperature, °C)</span></p>
<p style='margin: 8px 0;'><b style='color: #e65100;'>x₂</b> <span style='color: #424242;'>= ẏ (rate of temperature change, °C/s)</span></p>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #e65100; font-size: 17px;'>Euler Integration:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #f57c00;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
x₂<sub>new</sub> = x₂<sub>old</sub> + Δt · ÿ<br>
x₁<sub>new</sub> = x₁<sub>old</sub> + Δt · x₂<sub>old</sub>
</p>
</div>

<div style='background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px dashed #ff6f00;'>
<p style='margin: 0; color: #e65100; font-size: 15px;'>
<b>⚠️ IMPORTANT:</b> x₁ is updated with the <b>OLD</b> value of x₂!
</p>
</div>
</div>
"""

    def _get_target_temperature_html(self) -> str:
        """Get target temperature HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<div style='background: #2e7d32; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u<sub>delayed</sub> + K<sub>z</sub>·(T<sub>out</sub> - T<sub>amb,ref</sub>)
</span>
</div>

<p style='margin: 12px 0 8px 0;'><b style='color: #2e7d32; font-size: 17px;'>де:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #388e3c;'>K</b> — коефіцієнт підсилення (heating gain)<br>
• <b style='color: #388e3c;'>u<sub>delayed</sub></b> — потік пари з запізненням L (delayed steam flow)<br>
• <b style='color: #388e3c;'>K<sub>z</sub></b> — коефіцієнт впливу зовнішньої температури<br>
• <b style='color: #388e3c;'>T<sub>out</sub></b> — зовнішня температура (°C)<br>
• <b style='color: #388e3c;'>T<sub>amb,ref</sub></b> — референсна температура навколишнього середовища (°C)
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<div style='background: #2e7d32; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u<sub>delayed</sub> + K<sub>z</sub>·(T<sub>out</sub> - T<sub>amb,ref</sub>)
</span>
</div>

<p style='margin: 12px 0 8px 0;'><b style='color: #2e7d32; font-size: 17px;'>where:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #388e3c;'>K</b> — heating gain coefficient<br>
• <b style='color: #388e3c;'>u<sub>delayed</sub></b> — delayed steam flow (with transport delay L)<br>
• <b style='color: #388e3c;'>K<sub>z</sub></b> — ambient temperature coupling coefficient<br>
• <b style='color: #388e3c;'>T<sub>out</sub></b> — outdoor temperature (°C)<br>
• <b style='color: #388e3c;'>T<sub>amb,ref</sub></b> — reference ambient temperature (°C)
</p>
</div>
</div>
"""

    def _get_transport_delay_html(self) -> str:
        """Get transport delay HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #f57f17; font-size: 17px;'>Кільцевий буфер (Ring Buffer):</b></p>
<div style='background: white; padding: 18px; border-radius: 8px; border-left: 4px solid #f9a825; margin-bottom: 15px;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
N = round(L / Δt) — розмір буфера<br><br>
u<sub>delayed</sub> = buffer[index]<br>
buffer[index] = u<sub>current</sub><br>
index = (index + 1) mod N
</p>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #f57f17; font-size: 17px;'>Параметри:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #f9a825;'>L</b> — час запізнення (секунди)<br>
• <b style='color: #f9a825;'>Δt</b> — крок інтегрування (секунди)
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #f57f17; font-size: 17px;'>Ring Buffer Implementation:</b></p>
<div style='background: white; padding: 18px; border-radius: 8px; border-left: 4px solid #f9a825; margin-bottom: 15px;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
N = round(L / Δt) — buffer size<br><br>
u<sub>delayed</sub> = buffer[index]<br>
buffer[index] = u<sub>current</sub><br>
index = (index + 1) mod N
</p>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #f57f17; font-size: 17px;'>Parameters:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #f9a825;'>L</b> — transport delay time (seconds)<br>
• <b style='color: #f9a825;'>Δt</b> — integration time step (seconds)
</p>
</div>
</div>
"""

    def _get_water_temperature_html(self) -> str:
        """Get water temperature HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #6a1b9a; font-size: 17px;'>Аперіодична ланка 1-го порядку:</b></p>
<div style='background: #7b1fa2; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
dT<sub>water</sub>/dt = (K<sub>UW</sub>·y - T<sub>water</sub>) / T<sub>W</sub>
</span>
</div>

<p style='margin: 12px 0 8px 0;'><b style='color: #6a1b9a; font-size: 17px;'>де:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #7b1fa2;'>K<sub>UW</sub></b> — коефіцієнт нагріву води<br>
• <b style='color: #7b1fa2;'>T<sub>W</sub></b> — постійна часу води (секунди)<br>
• <b style='color: #7b1fa2;'>y</b> — температура теплиці (вхід, °C)
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #6a1b9a; font-size: 17px;'>First-Order Aperiodic Element:</b></p>
<div style='background: #7b1fa2; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
dT<sub>water</sub>/dt = (K<sub>UW</sub>·y - T<sub>water</sub>) / T<sub>W</sub>
</span>
</div>

<p style='margin: 12px 0 8px 0;'><b style='color: #6a1b9a; font-size: 17px;'>where:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px;'>
<p style='margin: 10px 0; color: #424242;'>
• <b style='color: #7b1fa2;'>K<sub>UW</sub></b> — water heating coefficient<br>
• <b style='color: #7b1fa2;'>T<sub>W</sub></b> — water time constant (seconds)<br>
• <b style='color: #7b1fa2;'>y</b> — greenhouse temperature (input, °C)
</p>
</div>
</div>
"""

    def _get_parameters_table_html(self) -> str:
        """Get parameters table HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 15px; color: #212121;'>
<table style='width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;'>
<tr style='background: #37474f; color: white;'>
    <th style='padding: 14px; text-align: left; font-size: 16px;'>Параметр</th>
    <th style='padding: 14px; text-align: left; font-size: 16px;'>Опис</th>
    <th style='padding: 14px; text-align: center; font-size: 16px;'>Типове значення</th>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Коефіцієнт підсилення</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>41.67</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>T₁</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Перша постійна часу</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>120.0 с</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>T₂</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Друга постійна часу</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>60.0 с</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>L</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Час запізнення</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>10.0 с</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K<sub>z</sub></b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Коефіцієнт зовнішньої температури</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>1.0</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K<sub>UW</sub></b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Коефіцієнт нагріву води</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>0.5</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px;'><b style='color: #1976d2; font-size: 16px;'>T<sub>W</sub></b></td>
    <td style='padding: 12px; color: #424242;'>Постійна часу води</td>
    <td style='padding: 12px; text-align: center; color: #424242;'><b>90.0 с</b></td>
</tr>
</table>
</div>
"""
        else:
            return """
<div style='font-size: 15px; color: #212121;'>
<table style='width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;'>
<tr style='background: #37474f; color: white;'>
    <th style='padding: 14px; text-align: left; font-size: 16px;'>Parameter</th>
    <th style='padding: 14px; text-align: left; font-size: 16px;'>Description</th>
    <th style='padding: 14px; text-align: center; font-size: 16px;'>Typical Value</th>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Heating gain coefficient</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>41.67</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>T₁</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>First time constant</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>120.0 s</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>T₂</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Second time constant</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>60.0 s</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>L</b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Transport delay time</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>10.0 s</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K<sub>z</sub></b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Ambient temperature coupling</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>1.0</b></td>
</tr>
<tr style='background: white;'>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'><b style='color: #1976d2; font-size: 16px;'>K<sub>UW</sub></b></td>
    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0; color: #424242;'>Water heating coefficient</td>
    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; color: #424242;'><b>0.5</b></td>
</tr>
<tr style='background: #f5f5f5;'>
    <td style='padding: 12px;'><b style='color: #1976d2; font-size: 16px;'>T<sub>W</sub></b></td>
    <td style='padding: 12px; color: #424242;'>Water time constant</td>
    <td style='padding: 12px; text-align: center; color: #424242;'><b>90.0 s</b></td>
</tr>
</table>
</div>
"""

    def _get_transfer_function_html(self) -> str:
        """Get transfer function HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #ad1457; font-size: 17px;'>Передавальна функція H(s):</b></p>
<div style='background: #c2185b; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
H(s) = 1 / (T₁·T₂·s² + (T₁+T₂)·s + 1)
</span>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #ad1457; font-size: 17px;'>Полюси системи:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #c2185b; margin-bottom: 15px;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
s₁ = -1/T₁ ≈ -0.00833<br>
s₂ = -1/T₂ ≈ -0.01667
</p>
</div>

<div style='background: #c8e6c9; padding: 15px; border-radius: 8px; border: 2px solid #2e7d32;'>
<p style='margin: 0; color: #1b5e20; font-size: 16px;'>
<b>✓ Обидва полюси від'ємні → система стабільна</b>
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 16px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 12px;'><b style='color: #ad1457; font-size: 17px;'>Transfer Function H(s):</b></p>
<div style='background: #c2185b; padding: 20px; border-radius: 10px; margin-bottom: 18px;'>
<span style='color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
H(s) = 1 / (T₁·T₂·s² + (T₁+T₂)·s + 1)
</span>
</div>

<p style='margin: 16px 0 8px 0;'><b style='color: #ad1457; font-size: 17px;'>System Poles:</b></p>
<div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #c2185b; margin-bottom: 15px;'>
<p style='margin: 8px 0; font-size: 17px; color: #424242;'>
s₁ = -1/T₁ ≈ -0.00833<br>
s₂ = -1/T₂ ≈ -0.01667
</p>
</div>

<div style='background: #c8e6c9; padding: 15px; border-radius: 8px; border: 2px solid #2e7d32;'>
<p style='margin: 0; color: #1b5e20; font-size: 16px;'>
<b>✓ Both poles are negative → system is stable</b>
</p>
</div>
</div>
"""

    def _get_formula_comparison_html(self) -> str:
        """Get formula comparison HTML"""
        if self.language == 'uk':
            return """
<div style='font-size: 15px; line-height: 2.0; color: #212121;'>
<div style='background: #ffcdd2; padding: 18px; border-radius: 10px; border: 3px solid #c62828; margin-bottom: 20px;'>
<p style='margin: 0 0 12px 0;'><b style='color: #b71c1c; font-size: 18px;'>❌ СТАРА ФОРМУЛА (НЕСТАБІЛЬНА):</b></p>
<div style='background: white; padding: 15px; border-radius: 6px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·y + K·u + K<sub>z</sub>·T<sub>out</sub>
</span>
</div>
<p style='margin: 15px 0 0 0; color: #c62828; font-size: 15px;'>
<b>Проблема:</b> Постійний вхід K·u + K<sub>z</sub>·T<sub>out</sub> накопичується в інтеграторі →
температура зростає до ∞ (було <b>2863°C</b>!)
</p>
</div>

<div style='background: #c8e6c9; padding: 18px; border-radius: 10px; border: 3px solid #2e7d32;'>
<p style='margin: 0 0 12px 0;'><b style='color: #1b5e20; font-size: 18px;'>✓ НОВА ФОРМУЛА (СТАБІЛЬНА):</b></p>
<div style='background: white; padding: 15px; border-radius: 6px; margin-bottom: 12px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u + K<sub>z</sub>·T<sub>out</sub>
</span>
</div>
<div style='background: white; padding: 15px; border-radius: 6px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·(y - y<sub>target</sub>)
</span>
</div>
<p style='margin: 15px 0 0 0; color: #1b5e20; font-size: 15px;'>
<b>Рішення:</b> Система відстежує цільову точку y<sub>target</sub> →
температура стабілізується на <b>~35°C</b> ✓
</p>
</div>
</div>
"""
        else:
            return """
<div style='font-size: 15px; line-height: 2.0; color: #212121;'>
<div style='background: #ffcdd2; padding: 18px; border-radius: 10px; border: 3px solid #c62828; margin-bottom: 20px;'>
<p style='margin: 0 0 12px 0;'><b style='color: #b71c1c; font-size: 18px;'>❌ OLD FORMULA (UNSTABLE):</b></p>
<div style='background: white; padding: 15px; border-radius: 6px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·y + K·u + K<sub>z</sub>·T<sub>out</sub>
</span>
</div>
<p style='margin: 15px 0 0 0; color: #c62828; font-size: 15px;'>
<b>Problem:</b> Constant input K·u + K<sub>z</sub>·T<sub>out</sub> accumulates in integrator →
temperature grows to ∞ (was <b>2863°C</b>!)
</p>
</div>

<div style='background: #c8e6c9; padding: 18px; border-radius: 10px; border: 3px solid #2e7d32;'>
<p style='margin: 0 0 12px 0;'><b style='color: #1b5e20; font-size: 18px;'>✓ NEW FORMULA (STABLE):</b></p>
<div style='background: white; padding: 15px; border-radius: 6px; margin-bottom: 12px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
y<sub>target</sub> = K·u + K<sub>z</sub>·T<sub>out</sub>
</span>
</div>
<div style='background: white; padding: 15px; border-radius: 6px;'>
<span style='font-size: 16px; color: #424242; font-family: "Cambria Math", serif;'>
ÿ = -(1/T₁ + 1/T₂)·ẏ - (1/(T₁·T₂))·(y - y<sub>target</sub>)
</span>
</div>
<p style='margin: 15px 0 0 0; color: #1b5e20; font-size: 15px;'>
<b>Solution:</b> System tracks target setpoint y<sub>target</sub> →
temperature stabilizes at <b>~35°C</b> ✓
</p>
</div>
</div>
"""
