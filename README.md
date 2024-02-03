Pour voir les différentes commandes :

    python3 diplome.py

### Question 1

Cacher un message :

    python3 diplome.py cache_texte diplome-BG diplome-hidden "Je suis là"

Récupèrer le message :

    python3 diplome.py recupere_texte diplome-hidden

### Question 2

Pour créer une paire de clés privées/publique :

    python3 diplome.py create_keys universite

Cette paire de clé nous permettra de signer nos diplomes pour certifier qu'ils sont vrais.

Pour signer un diplome :

    python3 diplome.py sign diplome-hidden.png

Le mot de passe est celui choisit lors de la création de paire de clés privées/publiques.

Pour vérifier un diplome :

    python3 diplome.py verif_sign diplome-hidden.png

### Question 3

Pour créer un diplome simple sans composant cryptographique :

    python3 diplome.py generate_diplome simple-diplome Pierre Hyvernat 19.5

### Question 4

Pour générer un diplome, on a décidé d'encrypter les données cachées avec RSA.

Ainsi, un mot de passe est demandé pour crypter la donnée.
Cela nous permet d'avoir un mot de passe unique pour chaque étudiant.

Comme on signe également le diplome, le mot de passe des clés générées précèdemment seront à nouveau demandés. (universite)

Pour générer un diplome avec une information caché :

    python3 diplome.py generate_diplome_crypted crypted-diplome Pierre Hyvernat 19.5 hyvernat

### Question 5

Pour vérifier le diplome obtenu :

    python3 diplome.py verif_sign crypted-diplome.png

Pour récupèrer la donnée cachée : (qui est la date de création du diplome)

    python3 diplome.py get_data_diplome crypted-diplome Pierre Hyvernat hyvernat




### Mini projet


Nous avons crée une petite application web pour vérifier la validité des diplomes.
Le QR code du diplome est scanné et une redirection sur une appli web minimale sera effectué.
Il faut ensuite upload l'image via le formulaire et le site va alors vérifier la signature du diplome via le script python grace a la clé privée générée via le script python.

Il faut réaliser les étapes des questions précédentes au préalable.

Pistes d'améliorations :
- Utiliser une base de données pour stocker les clés publiques.

Limites :
- La vérification de la signature est faite en local, il faudrait la faire sur le serveur pour plus de sécurité.
- La vérification de la signature est faite en python, via le même script pour générer et vérifier la clé.