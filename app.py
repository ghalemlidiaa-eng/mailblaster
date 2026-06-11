import streamlit as st
import pandas as pd
import smtplib
import os
import time
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

FICHIER_CONFIG = "config_mailblaster.json"

def charger_config():
    if os.path.exists(FICHIER_CONFIG):
        with open(FICHIER_CONFIG, "r") as f:
            return json.load(f)
    return {"email": "", "mdp": ""}

def sauvegarder_config(email, mdp):
    with open(FICHIER_CONFIG, "w") as f:
        json.dump({"email": email, "mdp": mdp}, f)

config = charger_config()

st.set_page_config(page_title="MailBlaster", page_icon="🚀", layout="centered")

st.title("🚀 MailBlaster")
st.subheader("L'outil universel pour automatiser tes candidatures")
st.markdown("---")

st.header("1. Tes identifiants de messagerie")
col1, col2 = st.columns(2)

with col1:
    email_utilisateur = st.text_input("Ton adresse e-mail (Gmail)", value=config["email"], placeholder="ton.nom@gmail.com")
with col2:
    mdp_utilisateur = st.text_input("Ton mot de passe d'application", value=config["mdp"], type="password", placeholder="abcd efgh ijkl mnop")

if st.button("💾 Enregistrer mes identifiants pour la prochaine fois"):
    sauvegarder_config(email_utilisateur, mdp_utilisateur)
    st.success("🔒 Identifiants sauvegardés en mémoire !")

st.markdown("---")

st.header("2. Tes documents")
st.markdown("""
**Format requis pour ton Excel :** Il doit contenir deux colonnes nommées exactement `Entreprise` et `Mail / Contact Web`.
""")

fichier_excel = st.file_uploader("Importe ta liste d'entreprises (Excel ou CSV)", type=["xlsx", "xls", "csv"])
pieces_jointes = st.file_uploader("Ajoute tes pièces jointes (CV, Lettre...)", type=["pdf", "docx", "png", "jpg"], accept_multiple_files=True)

st.header("3. Ton message personnalisé")
sujet_mail = st.text_input("Sujet de l'e-mail", placeholder="Ex: Candidature - Recherche d'alternance")

texte_par_defaut = """Bonjour,

Je me permets de vous contacter car je souhaite vivement postuler au sein de votre entreprise, {nom_entreprise}. 

Actuellement à la recherche d'une opportunité, je pense que mon profil correspond à vos besoins. Vous trouverez ci-joint mon CV ainsi que mes documents de candidature.

Je me tiens à votre entière disposition pour un entretien.

Cordialement,

[Ton Prénom] [Ton Nom]"""

corps_mail = st.text_area("Corps du message (Laisse bien la balise `{nom_entreprise}`)", value=texte_par_defaut, height=200)

st.markdown("---")

if st.button("🔥 LANCER L'ENVOI EN MASSE", use_container_width=True):
    if not email_utilisateur or not mdp_utilisateur:
        st.error("❌ Remplis tes identifiants.")
    elif not fichier_excel:
        st.error("❌ Il manque le fichier Excel.")
    elif not sujet_mail:
        st.error("❌ Il manque le sujet du mail.")
    else:
        try:
            if fichier_excel.name.endswith('.csv'):
                try:
                    df = pd.read_csv(fichier_excel, sep=';')
                except:
                    df = pd.read_csv(fichier_excel, sep=',')
            else:
                df = pd.read_excel(fichier_excel)

            if "Entreprise" not in df.columns or "Mail / Contact Web" not in df.columns:
                st.error("❌ Le fichier doit contenir les colonnes 'Entreprise' et 'Mail / Contact Web'.")
            else:
                st.warning("🔄 Connexion à Gmail...")
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(email_utilisateur, mdp_utilisateur)
                
                total_mails = len(df)
                barre_progression = st.progress(0)
                texte_statut = st.empty()
                envoyes_count = 0

                for index, ligne in df.iterrows():
                    nom_entreprise = str(ligne.get("Entreprise", "")).strip()
                    email_destinataire = str(ligne.get("Mail / Contact Web", "")).strip()

                    if not nom_entreprise or "@" not in email_destinataire:
                        envoyes_count += 1
                        barre_progression.progress(envoyes_count / total_mails)
                        continue

                    texte_statut.text(f"🚀 Envoi à {nom_entreprise}...")

                    msg = MIMEMultipart()
                    msg["From"] = email_utilisateur
                    msg["To"] = email_destinataire
                    msg["Subject"] = sujet_mail

                    texte_personnalise = corps_mail.replace("{nom_entreprise}", nom_entreprise)
                    msg.attach(MIMEText(texte_personnalise, "plain"))

                    if pieces_jointes:
                        for pj in pieces_jointes:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(pj.read())
                            encoders.encode_base64(part)
                            part.add_header("Content-Disposition", f"attachment; filename={pj.name}")
                            msg.attach(part)
                            pj.seek(0)

                    server.sendmail(email_utilisateur, email_destinataire, msg.as_string())
                    envoyes_count += 1
                    barre_progression.progress(envoyes_count / total_mails)
                    time.sleep(2)

                server.quit()
                texte_statut.empty()
                st.success("🎉 Toutes les candidatures ont été envoyées !")
                st.balloons()

        except Exception as e:
            st.error(f"❌ Erreur : {e}")