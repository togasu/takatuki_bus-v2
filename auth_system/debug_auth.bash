echo "bus_ID="
read bus_ID

export ID=$bus_ID
python3 auth.py
