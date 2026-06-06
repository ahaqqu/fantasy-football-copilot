"""Reference list of ~100 top World Cup 2026 players mapped to their country."""
# Used for matching player names in scraped expert articles.

PLAYERS_BY_COUNTRY = {
    # Argentina
    "Lionel Messi": "Argentina",
    "Julian Alvarez": "Argentina",
    "Enzo Fernandez": "Argentina",
    "Alexis Mac Allister": "Argentina",
    "Lautaro Martinez": "Argentina",
    "Julián Álvarez": "Argentina",
    "Emiliano Martinez": "Argentina",
    "Nahuel Molina": "Argentina",
    "Cristian Romero": "Argentina",
    "Rodrigo De Paul": "Argentina",

    # Brazil
    "Vinicius Junior": "Brazil",
    "Raphinha": "Brazil",
    "Endrick": "Brazil",
    "Rodrygo": "Brazil",
    "Alisson": "Brazil",
    "Marquinhos": "Brazil",
    "Bruno Guimaraes": "Brazil",
    "Lucas Paqueta": "Brazil",
    "Neymar": "Brazil",
    "Casemiro": "Brazil",

    # France
    "Kylian Mbappe": "France",
    "Ousmane Dembele": "France",
    "Antoine Griezmann": "France",
    "Aurelien Tchouameni": "France",
    "William Saliba": "France",
    "Theo Hernandez": "France",
    "Jules Kounde": "France",
    "Olivier Giroud": "France",
    "Mike Maignan": "France",
    "Nuno Mendes": "France",

    # England
    "Harry Kane": "England",
    "Jude Bellingham": "England",
    "Bukayo Saka": "England",
    "Phil Foden": "England",
    "Cole Palmer": "England",
    "Trent Alexander-Arnold": "England",
    "Declan Rice": "England",
    "Marcus Rashford": "England",
    "Jack Grealish": "England",
    "John Stones": "England",

    # Spain
    "Lamine Yamal": "Spain",
    "Pedri": "Spain",
    "Gavi": "Spain",
    "Dani Olmo": "Spain",
    "Alvaro Morata": "Spain",
    "Rodri": "Spain",
    "Alejandro Grimaldo": "Spain",
    "Unai Simon": "Spain",
    "Aymeric Laporte": "Spain",
    "Ferran Torres": "Spain",

    # Germany
    "Florian Wirtz": "Germany",
    "Jamal Musiala": "Germany",
    "Kai Havertz": "Germany",
    "Leroy Sane": "Germany",
    "Antonio Rudiger": "Germany",
    "Niclas Fullkrug": "Germany",
    "Toni Kroos": "Germany",
    "Joshua Kimmich": "Germany",
    "Manuel Neuer": "Germany",
    "Ilkay Gundogan": "Germany",

    # Portugal
    "Bruno Fernandes": "Portugal",
    "Cristiano Ronaldo": "Portugal",
    "Bernardo Silva": "Portugal",
    "Rafael Leao": "Portugal",
    "Diogo Jota": "Portugal",
    "Pepe": "Portugal",
    "Ruben Dias": "Portugal",
    "Vitinha": "Portugal",

    # Netherlands
    "Memphis Depay": "Netherlands",
    "Cody Gakpo": "Netherlands",
    "Denzel Dumfries": "Netherlands",
    "Virgil van Dijk": "Netherlands",
    "Frenkie de Jong": "Netherlands",
    "Xavi Simons": "Netherlands",
    "Martens Dumfries": "Netherlands",
    "Mathijs de Ligt": "Netherlands",

    # Belgium
    "Kevin De Bruyne": "Belgium",
    "Romelu Lukaku": "Belgium",
    "Jérémy Doku": "Belgium",
    "Leandro Trossard": "Belgium",
    "Thibaut Courtois": "Belgium",
    "Charles De Ketelaere": "Belgium",

    # Croatia
    "Luka Modric": "Croatia",
    "Mateo Kovacic": "Croatia",
    "Joško Gvardiol": "Croatia",
    "Marcelo Brozovic": "Croatia",
    "Ante Rebic": "Croatia",

    # Morocco
    "Achraf Hakimi": "Morocco",
    "Hakim Ziyech": "Morocco",
    "Youssef En-Nesyri": "Morocco",
    "Noussair Mazraoui": "Morocco",
    "Sofyan Amrabat": "Morocco",

    # Uruguay
    "Federico Valverde": "Uruguay",
    "Ronald Araujo": "Uruguay",
    "Darwin Nunez": "Uruguay",
    "Edinson Cavani": "Uruguay",
    "Rodrigo Bentancur": "Uruguay",
    "Manuel Ugarte": "Uruguay",

    # Japan
    "Takefusa Kubo": "Japan",
    "Kaoru Mitoma": "Japan",
    "Daichi Kamada": "Japan",
    "Wataru Endo": "Japan",
    "Takumi Minamino": "Japan",

    # South Korea
    "Son Heung-min": "South Korea",
    "Kim Min-jae": "South Korea",
    "Hwang Hee-chan": "South Korea",
    "Lee Kang-in": "South Korea",

    # USA
    "Christian Pulisic": "USA",
    "Weston McKennie": "USA",
    "Giovanni Reyna": "USA",
    "Folarin Balogun": "USA",
    "Tim Weah": "USA",
    "Malik Tillman": "USA",
    "Yunus Musah": "USA",

    # Mexico
    "Raul Jimenez": "Mexico",
    "Hirving Lozano": "Mexico",
    "Edson Alvarez": "Mexico",
    "Guillermo Ochoa": "Mexico",
    "Santiago Gimenez": "Mexico",

    # Senegal
    "Sadio Mane": "Senegal",
    "Ismaila Sarr": "Senegal",
    "Kalidou Koulibaly": "Senegal",
    "Edouard Mendy": "Senegal",

    # Canada
    "Alphonso Davies": "Canada",
    "Jonathan David": "Canada",
    "Tajon Buchanan": "Canada",

    # Australia
    "Mathew Ryan": "Australia",
    "Chris Wood": "Australia",

    # Switzerland
    "Granit Xhaka": "Switzerland",
    "Xherdan Shaqiri": "Switzerland",
    "Breel Embolo": "Switzerland",
    "Dan Ndoye": "Switzerland",

    # Ecuador
    "Moises Caicedo": "Ecuador",
    "Piero Hincapie": "Ecuador",
    "Enner Valencia": "Ecuador",

    # Serbia
    "Dusan Vlahovic": "Serbia",
    "Aleksandar Mitrovic": "Serbia",
    "Sergej Milinkovic-Savic": "Serbia",

    # Ghana
    "Thomas Partey": "Ghana",
    "Mohammed Kudus": "Ghana",
    "Inaki Williams": "Ghana",

    # Cameroon
    "Vincent Aboubakar": "Cameroon",
    "Eric Maxim Choupo-Moting": "Cameroon",

    # Tunisia
    "Wahbi Khazri": "Tunisia",

    # Iran
    "Mehdi Taremi": "Iran",
    "Sardar Azmoun": "Iran",

    # Saudi Arabia
    "Saud Abdulhamid": "Saudi Arabia",

    # Paraguay
    "Antonio Sanabria": "Paraguay",

    # Ivory Coast
    "Sebastian Haller": "Ivory Coast",
    "Nicolas Pepe": "Ivory Coast",

    # Algeria
    "Riyad Mahrez": "Algeria",
    "Ismael Bennacer": "Algeria",
    "Rayan Ait-Nouri": "Algeria",

    # Norway (didn't qualify but frequently mentioned in FPL context)
    "Erling Haaland": "Norway",
    "Martin Odegaard": "Norway",
}

# All country names for matching in text
COUNTRY_NAMES = list(set(PLAYERS_BY_COUNTRY.values()))

# Build reverse lookup: country -> list of players
PLAYERS_BY_COUNTRY_REVERSE = {}
for player, country in PLAYERS_BY_COUNTRY.items():
    if country not in PLAYERS_BY_COUNTRY_REVERSE:
        PLAYERS_BY_COUNTRY_REVERSE[country] = []
    PLAYERS_BY_COUNTRY_REVERSE[country].append(player)


def get_all_players() -> dict[str, str]:
    """Get all players (hardcoded + learned) merged."""
    from data.learned_store import get_all_players_merged
    return get_all_players_merged()
