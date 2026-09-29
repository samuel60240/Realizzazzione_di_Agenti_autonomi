import tkinter as tk
from gui import VacuumGUI

def main():
    root = tk.Tk()
    
    # Configure grid weights to allow resizing
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    
    # Set a minimum window size
    root.minsize(600, 400)
    
    app = VacuumGUI(root)
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
