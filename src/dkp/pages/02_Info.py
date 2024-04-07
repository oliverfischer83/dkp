import streamlit as st


def main():

    st.set_page_config(
        page_title="DKP - Info",
        page_icon="💰️",  # see https://twemoji-cheatsheet.vercel.app/
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.subheader("Regeln")
    st.markdown(
        """
    - Guthaben ...
      - `+100 DKP` als Startguthaben
      - `+50 DKP` pro Raidtag bei Raidende gutgeschrieben
      - darf nicht überzogen werden
      - ist Personen-gebunden
      - wird selbstständig kontrolliert
    - Verteilung ...
      - ein Gebot pro Spieler pro Item
      - bei Gleichstand entscheiden die Würfel
      - nur auf Items eigener Rüstungsklasse oder Rezepte bieten
      - Random Loot wird nicht verteilt
    """
    )

    st.subheader("Loot Addon")
    st.markdown(
        """
    - das Addon zum Verteilen des Raid-Loots heißt [RCLootCouncil](https://rclootcouncil.com/)
    - da wir keine Raid-Gilde sind, muss in den Addon Einstellungen (`/rc config`) die Option `Guild Groups Only` deaktiviert werden
    """
    )
    st.image("media/rclootcouncil_config.png", width=600)

    st.subheader("Wieso DKP?")
    st.markdown(
        """
    - DKP steht für Dragon Kill Points und ist ein System zur `gerechten Verteilung` von Loot in Raids.
    - Spieler erhalten die `Möglichkeit` sich ihr `Wunschitem` in gewisser Weise durch Raidteilnahme `zu erarbeiten`
    - die reine `Raidteilnahme wird belohnt`, unabhängig davon, ob Bosse gelegt wurden oder nicht
    - das Bieten auf Items und das Verwalten der eignen DKP bringt mehr \"Würze\" in den Raidalltag
    """
    )


# entry point
main()
