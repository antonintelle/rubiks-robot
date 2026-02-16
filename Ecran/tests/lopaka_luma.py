#!/usr/bin/env python3
"""
Convertisseur Lopaka C++ vers Python Luma
Convertit les fichiers générés par Lopaka vers du code Python utilisable avec luma.lcd
Compatible avec l'architecture Screen (base.py)
Sauvegarde les bitmaps en PNG avec transparence dans icons/
Usage: python3 lopaka_luma.py parametres_screen.cpp -o parametres.py
"""

import re
import sys
import argparse
from pathlib import Path
from PIL import Image

class LopakaToLuma:
    def __init__(self):
        self.bitmaps = []
        self.commands = []
        self.font_includes = set()
        self.current_color = "(255, 255, 255)"
        self.bitmap_dimensions = {}
        self.bitmap_colors = {}  # Stocker les couleurs des bitmaps
        
    def parse_bitmap(self, line):
        """Extrait les données bitmap d'une ligne C++"""
        match = re.search(r'(\w+)_bits\[\]\s*=\s*\{([^}]+)\}', line)
        if match:
            name = match.group(1)
            data = match.group(2)
            # Conversion des hex en bytes
            hex_values = re.findall(r'0x[0-9A-Fa-f]{2}', data)
            return name, hex_values
        return None, None
    
    def parse_command(self, line):
        """Parse une commande TFT"""
        line = line.strip()
        if not line.startswith('tft.'):
            return None
        
        # Enlever le tft. et le ;
        cmd = line[4:].rstrip(';')
        return cmd
    
    def rgb565_to_rgb888(self, color565):
        """Convertit RGB565 en RGB888"""
        if isinstance(color565, str):
            color565 = int(color565, 16)
        r = ((color565 >> 11) & 0x1F) * 255 // 31
        g = ((color565 >> 5) & 0x3F) * 255 // 63
        b = (color565 & 0x1F) * 255 // 31
        return f"({r}, {g}, {b})"
    
    def rgb565_to_tuple(self, color565):
        """Convertit RGB565 en tuple RGB"""
        if isinstance(color565, str):
            color565 = int(color565, 16)
        r = ((color565 >> 11) & 0x1F) * 255 // 31
        g = ((color565 >> 5) & 0x3F) * 255 // 63
        b = (color565 & 0x1F) * 255 // 31
        return (r, g, b)
    
    def parse_file(self, filepath):
        """Parse le fichier C++"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire les bitmaps
        for line in content.split('\n'):
            if '_bits[]' in line:
                name, data = self.parse_bitmap(line)
                if name:
                    self.bitmaps.append((name, data))
            
            # Vérifier les inclusions de fonts
            if '#include' in line and '.h' in line:
                match = re.search(r'#include\s*[<"]([^>"]+\.h)[>"]', line)
                if match:
                    font_file = match.group(1)
                    if 'font' in font_file.lower() or 'pt7b' in font_file.lower():
                        self.font_includes.add(font_file)
        
        # Extraire les commandes et les dimensions des bitmaps
        in_function = False
        for line in content.split('\n'):
            line = line.strip()
            if 'tft.' in line:
                in_function = True
            if in_function and line.startswith('tft.'):
                cmd = self.parse_command(line)
                if cmd:
                    self.commands.append(cmd)
                    
                    # Détecter les dimensions et couleurs des bitmaps depuis drawBitmap
                    if cmd.startswith('drawBitmap('):
                        match = re.search(r'drawBitmap\(\d+,\s*\d+,\s*(\w+)_bits,\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\)', cmd)
                        if match:
                            bitmap_name = match.group(1)
                            width = int(match.group(2))
                            height = int(match.group(3))
                            color = match.group(4)
                            self.bitmap_dimensions[bitmap_name] = (width, height)
                            self.bitmap_colors[bitmap_name] = self.rgb565_to_tuple(color)
    
    def _save_bitmaps_to_files(self):
        """Sauvegarde tous les bitmaps en PNG avec transparence dans icons/"""
        # Créer le dossier icons/ s'il n'existe pas
        icons_dir = Path('icons')
        icons_dir.mkdir(exist_ok=True)
        
        for name, hex_data in self.bitmaps:
            # Récupérer dimensions depuis les commandes drawBitmap
            dims = self.bitmap_dimensions.get(name, (32, 32))
            width, height = dims
            
            # Récupérer la couleur
            color = self.bitmap_colors.get(name, (255, 255, 255))
            
            # Convertir hex en bytes
            bits = bytes([int(h, 16) for h in hex_data])
            
            # Créer image RGBA (avec transparence)
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            pixels = img.load()
            
            for y in range(height):
                for x in range(width):
                    byte_idx = (y * ((width + 7) // 8)) + (x // 8)
                    if byte_idx < len(bits):
                        byte = bits[byte_idx]
                        bit = (byte >> (7 - (x % 8))) & 1
                        # Si bit = 1, dessiner avec la couleur + alpha 255
                        # Si bit = 0, laisser transparent
                        if bit:
                            pixels[x, y] = (*color, 255)
            
            # Nom du fichier (enlever préfixe "image_" si présent)
            clean_name = name.replace('image_', '')
            output_path = icons_dir / f"{clean_name}.png"
            
            # Sauvegarder en PNG
            img.save(output_path)
            print(f"  → Image sauvegardée: {output_path} ({width}x{height}, couleur {color})")
    
    def convert_command(self, cmd):
        """Convertit une commande TFT en code Luma"""
        # fillScreen
        if cmd.startswith('fillScreen('):
            match = re.search(r'fillScreen\((0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                color = self.rgb565_to_rgb888(match.group(1))
                return f"draw.rectangle((0, 0, self.gui.device.width-1, self.gui.device.height-1), fill={color})"
        
        # fillRoundRect
        elif cmd.startswith('fillRoundRect('):
            match = re.search(r'fillRoundRect\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                x, y, w, h, r, color = match.groups()
                x2 = int(x) + int(w)
                y2 = int(y) + int(h)
                color_rgb = self.rgb565_to_rgb888(color)
                return f"draw.rounded_rectangle(({x}, {y}, {x2}, {y2}), radius={r}, fill={color_rgb})"
        
        # drawLine
        elif cmd.startswith('drawLine('):
            match = re.search(r'drawLine\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                x1, y1, x2, y2, color = match.groups()
                color_rgb = self.rgb565_to_rgb888(color)
                return f"draw.line(({x1}, {y1}, {x2}, {y2}), fill={color_rgb}, width=1)"
        
        # drawRoundRect (rectangle arrondi sans remplissage)
        elif cmd.startswith('drawRoundRect('):
            match = re.search(r'drawRoundRect\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                x, y, w, h, r, color = match.groups()
                x2 = int(x) + int(w)
                y2 = int(y) + int(h)
                color_rgb = self.rgb565_to_rgb888(color)
                return f"draw.rounded_rectangle(({x}, {y}, {x2}, {y2}), radius={r}, outline={color_rgb}, width=1)"
        
        # setTextColor
        elif cmd.startswith('setTextColor('):
            match = re.search(r'setTextColor\((0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                self.current_color = self.rgb565_to_rgb888(match.group(1))
                return f"current_color = {self.current_color}"
        
        # setTextSize
        elif cmd.startswith('setTextSize('):
            return f"# {cmd}"
        
        # setFreeFont
        elif cmd.startswith('setFreeFont('):
            match = re.search(r'setFreeFont\(&(\w+)\)', cmd)
            if match:
                return f"# Police: {match.group(1)}"
            return "# Police par défaut"
        
        # drawString
        elif cmd.startswith('drawString('):
            match = re.search(r'drawString\("([^"]+)",\s*(\d+),\s*(\d+)\)', cmd)
            if match:
                text, x, y = match.groups()
                return f'draw.text(({x}, {y}), "{text}", fill=current_color, font=self.gui.font_small)'
        
        # drawBitmap
        elif cmd.startswith('drawBitmap('):
            match = re.search(r'drawBitmap\((\d+),\s*(\d+),\s*(\w+)_bits,\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+)\)', cmd)
            if match:
                x, y, name, w, h, color = match.groups()
                clean_name = name.replace('image_', '')
                return f'self.write_image(draw, {x}, {y}, "icons/{clean_name}.png")'
        
        return f"# Non converti: {cmd}"
    
    def generate_python(self, output_file=None):
        """Génère le code Python"""
        lines = []
        
        # Déduire le nom de la classe depuis le fichier
        class_name = "GeneratedScreen"
        if output_file:
            # parametres.py -> ParametresScreen
            base_name = Path(output_file).stem
            class_name = ''.join(word.capitalize() for word in base_name.split('_')) + 'Screen'
        
        # Sauvegarder les bitmaps en PNG
        if self.bitmaps:
            print("→ Sauvegarde des images PNG...")
            self._save_bitmaps_to_files()
        
        # En-tête
        lines.append("# Généré automatiquement par lopaka_luma")
        lines.append("from .base import Screen, HEADER_HEIGHT, BLACK, WHITE")
        lines.append("")
        
        # Note sur les fonts
        if self.font_includes:
            lines.append("# Fonts détectées:")
            for font in self.font_includes:
                lines.append(f"# - {font}")
            lines.append("# Note: Intégrez manuellement les polices GFX si nécessaire")
            lines.append("")
        
        # Classe Screen
        lines.append(f"class {class_name}(Screen):")
        lines.append("    def __init__(self, gui):")
        lines.append(f"        super().__init__(gui, title=\"{class_name.replace('Screen', '')}\")")
        lines.append("")
        
        # Ajouter le bouton retour si présent
        if any('back' in name for name, _ in self.bitmaps):
            lines.append("        # Bouton retour")
            lines.append("        x_back, y_back = self.get_position('rd', obj_size=(24,24), margin=5)")
            lines.append("        self.btn_back = self.add_button(")
            lines.append("            rect=(x_back, y_back, x_back + 24, y_back + 24),")
            lines.append('            on_click=lambda: self.gui.set_screen("home")')
            lines.append("        )")
            lines.append("")
        
        # Méthode render_body
        lines.append("    def render_body(self, draw, header_h: int):")
        lines.append("        \"\"\"Rendu du corps de l'écran\"\"\"")
        lines.append("        current_color = (255, 255, 255)")
        lines.append("")
        
        # Commandes converties
        for cmd in self.commands:
            converted = self.convert_command(cmd)
            lines.append(f"        {converted}")
        
        lines.append("")
        
        # Écrire dans le fichier ou stdout
        output = '\n'.join(lines)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ Fichier généré: {output_file}")
            print(f"✓ Classe créée: {class_name}")
        else:
            print(output)

def main():
    parser = argparse.ArgumentParser(
        description='Convertit un fichier Lopaka C++ en Python Luma (format Screen)',
        epilog='Exemple: python3 lopaka_luma.py parametres_screen.cpp -o parametres.py'
    )
    parser.add_argument('input', help='Fichier C++ d\'entrée (Lopaka)')
    parser.add_argument('-o', '--output', help='Fichier Python de sortie')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier existe
    if not Path(args.input).exists():
        print(f"✗ Erreur: Le fichier '{args.input}' n'existe pas")
        sys.exit(1)
    
    # Convertir
    print(f"→ Conversion de {args.input}...")
    converter = LopakaToLuma()
    converter.parse_file(args.input)
    
    if not converter.commands:
        print("⚠ Attention: Aucune commande TFT trouvée dans le fichier")
    
    converter.generate_python(args.output)
    print("✓ Conversion terminée")
    print("\n📝 N'oubliez pas d'importer votre écran dans main.py:")
    if args.output:
        class_name = ''.join(word.capitalize() for word in Path(args.output).stem.split('_')) + 'Screen'
        module_name = Path(args.output).stem
        print(f"   from screens.{module_name} import {class_name}")
        print(f"   gui.add_screen('{module_name}', {class_name}(gui))")

if __name__ == '__main__':
    main()
