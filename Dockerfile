FROM ubuntu:latest

# Éviter les invites interactives pendant l’installation
ENV DEBIAN_FRONTEND=noninteractive

# Mise à jour et installation des paquets nécessaires pour créer le chroot
RUN apt-get update && apt-get install -y \
    debootstrap \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire qui servira de jail chroot pour l'utilisateur 'welcome'
RUN mkdir -p /home/welcome/chroot

# Utiliser debootstrap pour créer un système minimal (Ubuntu focal) dans la jail avec les composants main et universe
RUN debootstrap --components=main,universe focal /home/welcome/chroot http://archive.ubuntu.com/ubuntu

# Installer les paquets essentiels dans l'environnement chroot (bash, passwd, gobuster et sqlmap)
RUN chroot /home/welcome/chroot apt-get update && \
    chroot /home/welcome/chroot apt-get install -y bash passwd gobuster sqlmap python3 python3-pip nano

# Créer l'utilisateur 'welcome' dans le chroot avec son répertoire personnel et son shell
RUN chroot /home/welcome/chroot useradd -ms /bin/bash welcome

# Copier les fichiers nécessaires dans le chroot
COPY SQLPaf.sh /home/welcome/chroot/home/welcome/
COPY requirements.txt /home/welcome/chroot/home/welcome/
COPY src /home/welcome/chroot/home/welcome/src
COPY bin /home/welcome/chroot/home/welcome/bin

# Assurer que les fichiers appartiennent à l'utilisateur 'welcome' dans le chroot
RUN chroot /home/welcome/chroot chown -R welcome:welcome /home/welcome

# Créer un script d'entrée pour lancer automatiquement le chroot et se connecter sous l'utilisateur 'welcome'
RUN echo '#!/bin/bash\nchroot /home/welcome/chroot su - welcome' > /entrypoint.sh && chmod +x /entrypoint.sh

# Lancer le script d'entrée au démarrage du conteneur
ENTRYPOINT ["/entrypoint.sh"]