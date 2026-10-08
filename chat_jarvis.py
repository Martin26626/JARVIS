import tkinter as tk
from tkinter import scrolledtext
import threading
import jarvis


class ChatJARVIS:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS - Chat")
        self.root.geometry("700x600")

        # Historial
        self.chat = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            state="disabled",
            font=("Segoe UI", 11)
        )
        self.chat.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=(10, 5)
        )

        # Entrada
        frame = tk.Frame(root)
        frame.pack(fill=tk.X, padx=10, pady=10)

        self.entrada = tk.Entry(
            frame,
            font=("Segoe UI", 12)
        )
        self.entrada.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        self.entrada.bind("<Return>", self.enviar)

        self.boton = tk.Button(
            frame,
            text="Enviar",
            command=self.enviar,
            width=10
        )
        self.boton.pack(side=tk.RIGHT, padx=(5, 0))

        self.escribir_chat(
            "JARVIS",
            "Listo, señor Martín. Puede escribirme."
        )

    def escribir_chat(self, quien, texto):
        self.chat.config(state="normal")
        self.chat.insert(
            tk.END,
            f"{quien}: {texto}\n\n"
        )
        self.chat.config(state="disabled")
        self.chat.see(tk.END)

    def enviar(self, event=None):
        texto = self.entrada.get().strip()

        if not texto:
            return

        self.entrada.delete(0, tk.END)

        self.escribir_chat("TÚ", texto)

        self.boton.config(state="disabled")

        threading.Thread(
            target=self.procesar,
            args=(texto,),
            daemon=True
        ).start()

    def procesar(self, texto):
        try:
            accion = jarvis.detectar_accion(texto)

            if accion:
                respuesta = jarvis.ejecutar_accion(
                    accion,
                    lambda mensaje, tipo="info": None
                )
            else:
                respuesta = jarvis.preguntar_ollama(texto)

            self.root.after(
                0,
                self.mostrar_respuesta,
                respuesta
            )

        except Exception as e:
            self.root.after(
                0,
                self.mostrar_respuesta,
                f"Ocurrió un error: {e}"
            )

    def mostrar_respuesta(self, respuesta):
        self.escribir_chat("JARVIS", respuesta)

        # JARVIS habla la respuesta
        threading.Thread(
            target=jarvis.hablar,
            args=(respuesta,),
            daemon=True
        ).start()

        self.boton.config(state="normal")
        self.entrada.focus()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatJARVIS(root)
    root.mainloop()