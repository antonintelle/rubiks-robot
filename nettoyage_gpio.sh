#!/bin/bash
echo "🔍 Diagnostic GPIO..."

echo "1. Processus Python actifs :"
ps aux | grep python | grep -v grep

echo ""
echo "2. Permissions GPIO :"
ls -l /dev/gpiomem

echo ""
echo "3. Groupes utilisateur :"
groups

echo ""
echo "4. Tentative de nettoyage complet..."
sudo pkill -9 python3
sleep 1

sudo python3 << 'EOF'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
pins = [5, 6, 13, 19, 26, 16, 23, 24]
for pin in pins:
    try:
        GPIO.cleanup(pin)
    except:
        pass
GPIO.cleanup()
print("✅ Nettoyage effectué")
EOF
