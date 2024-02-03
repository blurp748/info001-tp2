from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import sys
import subprocess
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from bitstring import BitArray

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
        - generate_diplome <NEW_FILE> <PRENOM> <NOM> <MOYENNE>
                Generate a new diplome.
        - generate_diplome_crypted <NEW_FILE> <PRENOM> <NOM> <MOYENNE> <PASSWORD>
                Generate a new crypted diplome (with date).
                
        - generate_qr_code <FILE> <URL>
        """)

def checkArgs(number, command):
    if(args != number):
        print(command)
        exit(1)

def cache_texte(image, new_image, texte):
    img = Image.open(image + '.png')

    pixels = img.load()
    largeur, hauteur = img.size
    nb_pixel = largeur * hauteur

    if len(texte) > 0:
        spaces = 10000 - len(texte)
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
            if(cpt < 80000):
                r, g, b, z = pixels[i, j]
                binary_red = '{0:08b}'.format(r)
                binary_texte += str(binary_red[len(binary_red) - 1])
                cpt+=1


    text = [binary_texte[i:i+8] for i in range(0, len(binary_texte), 8)]
    text = "".join([chr(int(binary_texte[i:i+8], 2)) for i in range(0, len(binary_texte), 8)])
    text = text.rstrip()

    return text

def generate_private_key(keypass):
    print("Generating private key...")
    subprocess.run(["openssl", "genrsa", "-aes256", "-passout", f"pass:{keypass}", "-out", ".cle_privee.pem", "2048"])

def generate_public_key(keypass):
    print("Generating public key...")
    subprocess.run(["openssl", "rsa", "-in", ".cle_privee.pem", "-passin", f"pass:{keypass}", "-pubout", "-out", "cle_publique.pem"])
    subprocess.run(["cp", "cle_publique.pem", "./node"])


def RSA_keys(name, surname, keypass):

    key = RSA.generate(2048)
    name = name + "_" + surname + "_"
    private_key = key.export_key(passphrase=keypass, pkcs=8,
                              protection="scryptAndAES128-CBC",
                              prot_params={'iteration_count':131072})
    with open(name + "private.pem", "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(name + "receiver.pem", "wb") as f:
        f.write(public_key)

def encrypt_RSA(text, name, surname):
    from Crypto.Random import get_random_bytes
    import binascii

    data = text.encode("utf-8")

    recipient_key = RSA.import_key(open(name + "_" + surname + "_receiver.pem").read())
    session_key = get_random_bytes(16)

    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(session_key)

    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data)

    separator = "|||"
    hexadecimal_representation = binascii.hexlify(separator.encode())
    binary_separator = "11111000111110001111100"

    binary_enc_session_key = BitArray(bytes=enc_session_key).bin
    enc_session_key_binary = BitArray(bin=binary_enc_session_key).tobytes()

    binary_cipher_aes = BitArray(bytes=cipher_aes.nonce).bin
    binary_tag = BitArray(bytes=tag).bin
    binary_ciphertext = BitArray(bytes=ciphertext).bin

    return binary_enc_session_key + binary_separator + binary_cipher_aes + binary_separator + binary_tag + binary_separator + binary_ciphertext

def decrypt_RSA(text, name, surname, password):

    private_key = RSA.import_key(open(name + "_" + surname + "_private.pem").read(), password)

    text = text.split("11111000111110001111100")

    enc_session_key = BitArray(bin=text[0]).tobytes()
    nonce = BitArray(bin=text[1]).tobytes()
    tag = BitArray(bin=text[2]).tobytes()
    ciphertext = BitArray(bin=text[3]).tobytes()

    # Decrypt the session key with the private RSA key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    data = cipher_aes.decrypt_and_verify(ciphertext, tag)
    print(data.decode("utf-8"))

def sign_file(file_path):
    subprocess.run(["openssl", "dgst", "-sha256", "-sign", ".cle_privee.pem", "-out", f"{file_path}.sig", file_path])
    subprocess.run(["cp", f"{file_path}.sig", "./node"])


def verify_signature(file_path):
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", "cle_publique.pem", "-signature", f"{file_path}.sig", file_path])

def generateDiploma(new_image, name, surname, moyenne):
    from datetime import date
    import random
    import qrcode
    today = date.today()

    img = Image.open("diplome-BG.png")           # ouverture de l'image
    fontSize = 4
    def add_text(text, x, y, font_size=fontSize, font_style="sans.ttf"):
        draw = ImageDraw.Draw(img)                  # objet "dessin" dans l'image
        font = ImageFont.truetype(font_style, font_size)
        draw.text((x, y), text, "black", font)       # ajout du texte

    # add text at the middle of the image
    width, height = img.size

    Diplome = "Master Informatique"
    add_text(Diplome, (width/2) - 210, height/5, fontSize*12)

    text = "Délivré à " + name + " " + surname
    add_text(text, (width//4), height/2.5, fontSize*8)

    moyenne = "Avec une moyenne de " + moyenne
    add_text(moyenne, (width//4), height/2, fontSize*8)

    img.save(new_image + '.png')            # sauvegarde de l'image obtenue dans un autre fichier

def generateDiplomaCrypted(new_image, name, surname, moyenne, password):
    from datetime import date

    RSA_keys(name, surname, password)

    generateDiploma(new_image, name, surname, moyenne)

    today = date.today().strftime("%d/%m/%Y")
    today = encrypt_RSA(today, name, surname)

    cache_texte(new_image, new_image, today)

    sign_file(new_image + '.png')


def addQrCode(image, url):
    import qrcode
    img = Image.open(image + '.png')
    # put the qr code in the top right corner it should be 1/4 of the image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white")
    img.paste(img_qr, (img.size[0] - img_qr.size[0], 0))
    img.save(image + '.png')



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

        text = recupere_texte(sys.argv[2])
        print(text)

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
        
        checkArgs(6, "generate_diplome <NEW_FILE> <PRENOM> <NOM> <MOYENNE>")

        generateDiploma(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    elif(commande == "generate_diplome_crypted"):

        checkArgs(7, "generate_diplome_crypted <NEW_FILE> <PRENOM> <NOM> <MOYENNE> <PASSWORD>")

        generateDiplomaCrypted(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])

    elif(commande == "get_data_diplome"):

        checkArgs(6, "get_data_diplome <FILE> <PRENOM> <NOM> <PASSWORD>")

        res = recupere_texte(sys.argv[2])
        decrypt_RSA(res, sys.argv[3], sys.argv[4], sys.argv[5])

    elif(commande == "generate_qr_code"):

        checkArgs(4, "generate_qr_code <FILE> <URL>")

        addQrCode(sys.argv[2], sys.argv[3])

    else:
        print("Command not found.")
