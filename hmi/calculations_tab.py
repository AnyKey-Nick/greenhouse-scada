"""
Calculations Tab - Thermal Process Analysis
===========================================

Tab showing thermal calculations and analysis.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit,
                              QScrollArea, QFrame, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CalculationsTab(QWidget):
    """Tab displaying thermal process calculations and analysis"""

    def __init__(self, parent=None, language='en'):
        super().__init__(parent)
        self.language = language
        self.setup_ui()

    def set_language(self, language: str):
        """Update language and refresh UI"""
        self.language = language
        self.setup_ui()

    def setup_ui(self):
        """Setup calculations display UI"""
        # Clear existing layout
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title_text = {
            'en': "Thermal Process Analysis & Calculations",
            'uk': "Аналіз та розрахунок теплових процесів"
        }
        title = QLabel(title_text[self.language])
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #d32f2f; padding: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(25)

        # Add calculation sections
        sections = [
            ('steam_flow', '#e3f2fd', '#1976d2'),
            ('time_constants', '#fff3e0', '#f57c00'),
            ('transfer_coefficients', '#e8f5e9', '#388e3c'),
            ('mathematical_model', '#f3e5f5', '#7b1fa2'),
            ('transfer_function', '#fce4ec', '#c2185b'),
            ('delay_time', '#fff9c4', '#f9a825'),
            ('transition_characteristics', '#e0f2f1', '#00897b'),
            ('quality_indicators', '#fce4ec', '#d81b60'),
        ]

        for section_key, bg_color, accent_color in sections:
            card = self._create_card(
                self._get_section_title(section_key),
                self._get_section_html(section_key),
                bg_color,
                accent_color
            )
            content_layout.addWidget(card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_card(self, title: str, html: str, bg_color: str, accent_color: str) -> QFrame:
        """Create modern card for calculations"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: none;
            }}
        """)

        # Add shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
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

        # Content
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

        text_edit.setMinimumHeight(220)
        layout.addWidget(text_edit)

        return card

    def _lighten_color(self, color: str) -> str:
        """Lighten hex color"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_section_title(self, key: str) -> str:
        """Get section title"""
        titles = {
            'en': {
                'steam_flow': "💨 Steam Flow Calculation",
                'time_constants': "⏱️ Time Constants",
                'transfer_coefficients': "📊 Transfer Coefficients",
                'mathematical_model': "🧮 Mathematical Model",
                'transfer_function': "📈 Transfer Function",
                'delay_time': "⏲️ Delay Time Analysis",
                'transition_characteristics': "📉 Transition Characteristics",
                'quality_indicators': "✅ Quality Indicators",
            },
            'uk': {
                'steam_flow': "💨 Розрахунок витрат пари",
                'time_constants': "⏱️ Сталі часу",
                'transfer_coefficients': "📊 Коефіцієнти передачі",
                'mathematical_model': "🧮 Математична модель",
                'transfer_function': "📈 Передавальна функція",
                'delay_time': "⏲️ Аналіз часу запізнення",
                'transition_characteristics': "📉 Перехідні характеристики",
                'quality_indicators': "✅ Показники якості",
            }
        }
        return titles[self.language][key]

    def _get_section_html(self, key: str) -> str:
        """Get section HTML content"""
        if self.language == 'uk':
            return self._get_section_html_uk(key)
        else:
            return self._get_section_html_en(key)

    def _get_section_html_uk(self, key: str) -> str:
        """Get Ukrainian HTML content"""
        sections = {
            'steam_flow': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #1565c0; font-size: 17px;'>За рівнянням статики можна знайти витрати пари:</b></p>
<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin: 15px 0;'>
<p style='text-align: center; margin: 0;'>
<span style='font-size: 19px; color: #1976d2; font-weight: 600; font-family: "Cambria Math", serif;'>
F<sub>to</sub> = (α·S<sub>ct</sub>·(T<sub>cto</sub> - T<sub>po</sub>)) / r = <b>51.258</b>
</span>
</p>
</div>
<p style='margin-top: 15px; color: #424242;'>
Де <b>r</b> - прихована теплота пароутворення, що враховує необхідну кількість теплоти для нагрівання суміші.
</p>
</div>
""",
            'time_constants': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #e65100; font-size: 17px;'>Обчислимо сталі часу:</b></p>
<div style='background: white; padding: 18px; border-radius: 10px; margin: 12px 0; border-left: 4px solid #f57c00;'>
<p style='margin: 10px 0;'>
<b style='color: #f57c00;'>τ₁</b> = (m<sub>ct</sub>·C<sub>ct</sub>) / (α·S<sub>ct</sub>) = <b style='color: #d84315;'>0.0886707</b>
</p>
<p style='margin: 10px 0;'>
<b style='color: #f57c00;'>τ₂</b> = (m<sub>p</sub>·C<sub>ct</sub>) / (α·S<sub>ct</sub>) = <b style='color: #d84315;'>0.6465846</b>
</p>
</div>
</div>
""",
            'transfer_coefficients': """
<div style='font-size: 15px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #2e7d32; font-size: 17px;'>Коефіцієнти передачі:</b></p>
<div style='background: #f5f5f5; padding: 15px; border-radius: 8px;'>
<p style='margin: 8px 0;'><b>K₁</b> = (r·F<sub>to</sub>) / (α·S<sub>ct</sub>·T<sub>cto</sub>)</p>
<p style='margin: 8px 0;'><b>K₂</b> = T<sub>po1</sub> / T<sub>cto</sub> = 11/80</p>
<p style='margin: 8px 0;'><b>K₃</b> = ((C<sub>p</sub>·T<sub>po</sub> - C<sub>p1</sub>·T<sub>po1</sub>)·F<sub>po</sub>) / ((C<sub>p1</sub>·F<sub>po</sub> + S<sub>ct</sub>·α)·T<sub>po1</sub>) = <b style='color: #c62828;'>-0.0005565</b></p>
<p style='margin: 8px 0;'><b>K₄</b> = (C<sub>p</sub>·F<sub>po</sub>·T<sub>po</sub>) / ((C<sub>p1</sub>·F<sub>po</sub> + S<sub>ct</sub>·α)·T<sub>po1</sub>) = <b style='color: #2e7d32;'>0.001209</b></p>
<p style='margin: 8px 0;'><b>K₅</b> = (α·S<sub>ct</sub>·T<sub>cto</sub>) / ((C<sub>p1</sub>·F<sub>po</sub> + S<sub>ct</sub>·α)·T<sub>po1</sub>) = <b style='color: #2e7d32;'>7.259889</b></p>
</div>
<div style='background: white; padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px solid #388e3c;'>
<p style='margin: 8px 0;'><b>τ<sub>II</sub></b> = (τ₁·τ₂) / (-K₂·K₅ + 1) = <b style='color: #1976d2;'>32.478</b></p>
<p style='margin: 8px 0;'><b>τ<sub>I</sub></b> = (τ₁ + τ₂) / (-K₂·K₅ + 1) = <b style='color: #1976d2;'>416.509</b></p>
<p style='margin: 8px 0;'><b>K₆</b> = (K₁·K₅) / (-K₂·K₅ + 1) = <b style='color: #1976d2;'>3547.119</b></p>
<p style='margin: 8px 0;'><b>K₇</b> = K₃ / (-K₂·K₅ + 1) = <b style='color: #c62828;'>-0.3153</b></p>
<p style='margin: 8px 0;'><b>K₈</b> = K₄ / (-K₂·K₅ + 1) = <b style='color: #2e7d32;'>0.6847</b></p>
</div>
</div>
""",
            'mathematical_model': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #6a1b9a; font-size: 17px;'>Математична модель кожухотрубного теплообмінника:</b></p>
<div style='background: linear-gradient(135deg, #7b1fa2 0%, #9c27b0 100%); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(123, 31, 162, 0.3);'>
<div style='background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;'>
<p style='text-align: center; margin: 0; color: white; font-size: 18px; font-weight: 600; font-family: "Cambria Math", serif;'>
32.47·(d²y/dt²) + 416.50·(dy₂/dt) + y₂ = 3547.11·x₁ + (-0.32)·(0.09·(dx₂/dt) + x₂) + 0.68·(0.09·(dz/dt) + z)
</p>
</div>
</div>
<div style='background: #fff3e0; padding: 18px; border-radius: 10px; margin-top: 18px; border-left: 4px solid #ff6f00;'>
<p style='margin: 0; color: #e65100; font-size: 15px;'>
<b>⚠️ Висновок:</b> Зв'язки між вихідним параметром y₂ і вхідним параметром x₂ та збуренням z є незначними і можуть бути проігноровані.
</p>
</div>
<p style='margin-top: 18px;'><b style='color: #6a1b9a;'>Спрощена модель:</b></p>
<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-top: 12px;'>
<p style='text-align: center; margin: 0; font-size: 18px; color: #7b1fa2; font-weight: 600; font-family: "Cambria Math", serif;'>
32.47·(d²y/dt²) + 416.50·(dy₂/dt) + y₂ = 3547.11
</p>
</div>
</div>
""",
            'transfer_function': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #ad1457; font-size: 17px;'>Передавальна функція за каналом регулювання:</b></p>
<div style='background: linear-gradient(135deg, #c2185b 0%, #d81b60 100%); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(194, 24, 91, 0.3);'>
<div style='background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;'>
<p style='text-align: center; margin: 0; color: white; font-size: 19px; font-weight: bold; font-family: "Cambria Math", serif;'>
W<sub>p</sub>(s) = 32.47 / (3547.11·s² + 416.50·s + 1)
</p>
</div>
</div>
<div style='background: #c8e6c9; padding: 18px; border-radius: 10px; margin-top: 18px; border: 2px solid #2e7d32;'>
<p style='margin: 0; color: #1b5e20; font-size: 15px;'>
<b>✓ Висновок:</b> Кожухотрубний теплообмінник описується диференційним рівнянням другого порядку. При відношенні τ'/√(τ'') = 73 > 2, перехідний процес є аперіодичним (без коливань).
</p>
</div>
</div>
""",
            'delay_time': """
<div style='font-size: 15px; line-height: 2.0; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #f57f17; font-size: 17px;'>Розрахунок часу запізнення:</b></p>
<div style='background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 12px 0;'>
<p style='margin: 10px 0;'><b>S<sub>t</sub></b> = (3.14/4)·D²<sub>vk</sub> - N·(3.14/4)·d²<sub>t</sub> = <b style='color: #f9a825;'>0.050416</b></p>
<p style='margin: 10px 0;'><b>V<sub>t</sub></b> = S<sub>t</sub>·l = <b style='color: #f9a825;'>0.08772</b></p>
<p style='margin: 10px 0;'><b>τ<sub>t</sub></b> = (V<sub>t</sub>·ρ) / F<sub>to</sub> = <b style='color: #f9a825;'>0.00210</b></p>
</div>
<div style='background: white; padding: 15px; border-radius: 8px; border: 2px solid #fbc02d;'>
<p style='margin: 10px 0;'><b>q</b> = m<sub>p</sub>·C<sub>p</sub>·(T<sub>cto</sub> - T<sub>po</sub>) = <b style='color: #f57c00;'>68336.55</b></p>
<p style='margin: 10px 0;'><b>τ<sub>ct</sub></b> = q / (α·S<sub>ct</sub>·(T<sub>cto</sub> - T<sub>po1</sub>)) = <b style='color: #f57c00;'>0.6364</b></p>
<p style='margin: 10px 0;'><b>τ<sub>f</sub></b> = τ<sub>t</sub> + τ<sub>ct</sub> = <b style='color: #d84315;'>0.6385</b></p>
</div>
<p style='margin-top: 18px;'><b style='color: #f57f17;'>Передавальна функція з запізненням:</b></p>
<div style='background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%); padding: 20px; border-radius: 10px; margin-top: 12px;'>
<p style='text-align: center; margin: 0; color: white; font-size: 18px; font-weight: 600; font-family: "Cambria Math", serif;'>
W<sub>p</sub>(s) = [32.47 / (3547.11·s² + 416.50·s + 1)]·e<sup>-2.19·s</sup>
</p>
</div>
</div>
""",
            'transition_characteristics': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #00897b; font-size: 17px;'>Перехідні характеристики:</b></p>
<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);'>
<p style='margin: 12px 0;'>
<b>W<sub>p</sub></b> = (K₆·e<sup>-τ<sub>f</sub>·s</sup>) / (τ<sub>II</sub>·s² + τ<sub>I</sub>·s + 1)
</p>
<p style='margin: 12px 0;'>
<b>W<sub>p</sub></b> = (3.547·e<sup>-0.6386·w</sup>) / (-32.478·w² + 416.509·w + 1)
</p>
</div>
<div style='background: #b2dfdb; padding: 18px; border-radius: 10px; margin-top: 18px;'>
<p style='margin: 0; color: #004d40; font-size: 15px;'>
<b>📊 Частотні характеристики:</b><br>
• ω<sub>кр1</sub> = 0.042<br>
• A(ω<sub>кр1</sub>) = 0.087<br>
• K<sub>p1</sub> = 0.5 / A(ω<sub>кр1</sub>) = <b>8.52</b>
</p>
</div>
<p style='margin-top: 18px;'><b style='color: #00897b;'>Передатна функція регулятора:</b></p>
<div style='background: linear-gradient(135deg, #00897b 0%, #00acc1 100%); padding: 20px; border-radius: 10px; margin-top: 12px;'>
<p style='text-align: center; margin: 0; color: white; font-size: 19px; font-weight: bold;'>
W<sub>p1</sub>(s) = K<sub>p1</sub> = 8.52
</p>
</div>
</div>
""",
            'quality_indicators': """
<div style='font-size: 15px; line-height: 2.2; color: #212121;'>
<p style='margin-bottom: 15px;'><b style='color: #c2185b; font-size: 17px;'>Показники якості перехідного процесу:</b></p>
<div style='background: linear-gradient(135deg, #f48fb1 0%, #f06292 100%); padding: 25px; border-radius: 12px;'>
<div style='background: white; padding: 20px; border-radius: 10px;'>
<p style='margin: 15px 0; font-size: 18px;'>
<b style='color: #880e4f;'>⏱️ Час регулювання:</b><br>
<span style='font-size: 32px; color: #c2185b; font-weight: bold;'>t<sub>p</sub> = 356 с</span>
</p>
<p style='margin: 15px 0; font-size: 18px;'>
<b style='color: #880e4f;'>📈 Перерегулювання:</b><br>
<span style='font-size: 32px; color: #c2185b; font-weight: bold;'>σ = 20%</span>
</p>
<p style='margin: 10px 0; color: #424242; font-size: 14px;'>
σ = (y<sub>max</sub> - y<sub>уст</sub>) / y<sub>уст</sub> × 100% = (1.43 - 1.17) / 1.17 × 100%
</p>
</div>
</div>
<div style='background: #c8e6c9; padding: 18px; border-radius: 10px; margin-top: 18px; border: 2px solid #2e7d32;'>
<p style='margin: 0; color: #1b5e20; font-size: 15px;'>
<b>✅ Висновок:</b> Обрані параметри регулятора забезпечують адекватну реакцію системи на зміни вхідного сигналу. Час регулювання визначає швидкість досягнення нового сталого стану, а перерегулювання відображає перевищення вихідного сигналу над встановленим значенням.
</p>
</div>
</div>
"""
        }
        return sections.get(key, "<p>Контент недоступний</p>")

    def _get_section_html_en(self, key: str) -> str:
        """Get English HTML content"""
        # Similar structure but in English
        return self._get_section_html_uk(key)  # For now, use Ukrainian version
