from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import sys
import subprocess

def help():
    print("""Commands
        - cache_texte <FILE_FROM> <FILE_TO> <MESSAGE>
                Hide text in image.
        - recupere_texte <FILE>
                Get hidden text form image.
        - create_keys <PASSWORD>
                Create Public and Private keys.
        - sign <FILE>
                Sign file with private key.
        - verif_sign <FILE>
                Verify signature from file with public key.
        - generate_diplome <NEW_FILE> <PRENOM> <NOM>
                Generate a new diplome.
        """)

def checkArgs(number, command):
    if(args != number):
        print(command)
        exit(1)

def cache_texte(image, new_image, texte):
    img = Image.open(image + '.png')

    texte = texte
    pixels = img.load()
    largeur, hauteur = img.size
    nb_pixel = largeur * hauteur

    if len(texte) > 0:
        spaces = 1000 - len(texte)
        texte = texte + (" " * spaces)

    # Convertir le texte en binaire
    binaire = ''.join(format(ord(char), '08b') for char in texte)
    taille_binaire = len(binaire)

    if taille_binaire > nb_pixel:
        raise ValueError("Text is too long")

    for i in range(largeur):
        for j in range(hauteur):
            if len(binaire) > 0:
                r, g, b, z = pixels[i, j]
                binary_red = '{0:08b}'.format(r)
                binary_red = binary_red[:-1]
                binary_red = binary_red + binaire[0]
                binary_red = int(binary_red, 2)
                binaire = binaire[1:]
                pixels[i, j] = binary_red, g, b, z

    img.save(new_image + '.png')

def recupere_texte(image):
    img = Image.open(image + '.png')

    pixels = img.load()
    largeur, hauteur = img.size
    nb_pixel = largeur * hauteur

    binary_texte = ""
    cpt = 0
    for i in range(largeur):
        for j in range(hauteur):
            if(cpt < 8000):
                r, g, b, z = pixels[i, j]
                binary_red = '{0:08b}'.format(r)
                binary_texte += str(binary_red[len(binary_red) - 1])
                cpt+=1


    text = [binary_texte[i:i+8] for i in range(0, len(binary_texte), 8)]
    text = "".join([chr(int(binary_texte[i:i+8], 2)) for i in range(0, len(binary_texte), 8)])
    text = text.rstrip()

    print(text)

def generate_private_key(keypass):
    print("Generating private key...")
    subprocess.run(["openssl", "genrsa", "-aes256", "-passout", f"pass:{keypass}", "-out", ".cle_privee.pem", "2048"])

def generate_public_key(keypass):
    print("Generating public key...")
    subprocess.run(["openssl", "rsa", "-in", ".cle_privee.pem", "-passin", f"pass:{keypass}", "-pubout", "-out", "cle_publique.pem"])

def sign_file(file_path):
    subprocess.run(["openssl", "dgst", "-sha256", "-sign", ".cle_privee.pem", "-out", f"{file_path}.sig", file_path])

def verify_signature(file_path):
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", "cle_publique.pem", "-signature", f"{file_path}.sig", file_path])

def generateDiploma(new_image, name, surname):
    from datetime import date
    import qrcode
    today = date.today()

    img = Image.open("diplome-BG.png")           # ouverture de l'image
    fontSize = 32
    def add_text(text, x, y, font_size=fontSize):
        draw = ImageDraw.Draw(img)                  # objet "dessin" dans l'image
        font = ImageFont.truetype("sans.ttf", fontSize)   # police à utiliser
        draw.text((x, y), text, "black", font)       # ajout du texte

    # add text at the middle of the image
    width, height = img.size

    Diplome = "Master 2 Informatique"
    add_text(Diplome, (width/2) - len(Diplome)*(fontSize//4), height/5, fontSize*8)

    text = "Délivré à"
    add_text(text, (width/2) - len(text) * fontSize, height/3, fontSize*8)

    name = name + " " + surname
    add_text(name, (width/2) - (len(name) * fontSize ) + len(text * (fontSize)), height/3, fontSize*8)

    date = "Le " + today.strftime("%d/%m/%Y")
    add_text(date, (width/2) - len(date)//2 * fontSize, height/1.5, fontSize*8)


    img.save(new_image + '.png')            # sauvegarde de l'image obtenue dans un autre fichier

    # QR code
    img = qrcode.make("https://www.youtube.com/shorts/leoN6ub1rKA")
    img.save(new_image + '_qr.png')

    # Paste QR code
    img = Image.open(new_image + '.png')
    qr = Image.open(new_image + '_qr.png')
    qrWidth, qrHeight = qr.size

    ## reduce QR code size
    qrWidth = int((qrWidth // 2.5) + 6)
    qrHeight = int((qrHeight // 2.5) + 6)
    qr = qr.resize((qrWidth, qrHeight))
    img.paste(qr, (width - qrWidth, 0))
    img.save(new_image + '.png')

# ====================================================================
# ============================== MAIN ================================
# ====================================================================

args = len(sys.argv)
if(args < 2):
    help()
else:
    commande = sys.argv[1]
    if(commande == "cache_texte"):

        checkArgs(5, "cache_texte <FILE_FROM> <FILE_TO> <MESSAGE>")

        cache_texte(sys.argv[2], sys.argv[3], sys.argv[4])

    elif(commande == "recupere_texte"):

        checkArgs(3, "recupere_texte <FILE>")

        recupere_texte(sys.argv[2])

    elif(commande == "create_keys"):
        
        checkArgs(3, "create_keys <PASSWORD>")

        keypass = sys.argv[2]
        generate_private_key(keypass)
        generate_public_key(keypass)

    elif(commande == "sign"):

        checkArgs(3, "sign <FILE>")

        sign_file(sys.argv[2])

    elif(commande == "verif_sign"):

        checkArgs(3, "verif_sign <FILE>")

        verify_signature(sys.argv[2])

    elif(commande == "generate_diplome"):
        
        checkArgs(5, "generate_diplome <NEW_FILE> <PRENOM> <NOM>")

        generateDiploma(sys.argv[2], sys.argv[3], sys.argv[4])
        
    else:
        print("Command not found.")
