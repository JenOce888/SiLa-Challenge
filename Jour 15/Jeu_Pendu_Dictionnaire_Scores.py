"""
main.py — Entry point
"""

import api
import ui


def main() -> None:
    api.start()
    app = ui.App()
    app.mainloop()


if __name__ == "__main__":
    main()
