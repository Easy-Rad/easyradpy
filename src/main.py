from ahk import AHK

def show_message():
    # Initialize AHK
    ahk = AHK(version="v2")
    
    # Show a message box directly using AHK
    ahk.msg_box('This is a test')

if __name__ == "__main__":
    show_message() 