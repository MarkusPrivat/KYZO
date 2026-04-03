from dataclasses import dataclass

from apps.kyzo_backend.config import UserRole, InputType

@dataclass(frozen=True)
class SeedData:
    """
    Provides static initialization data (seed data) for the Kyzo database.

    This class contains predefined datasets for users, subjects, topics,
    and raw question inputs. It is intended to be used for database
    initialization, migrations, or local development and testing.
    """

    # --- User Accounts ---
    USERS = [
        {
            "name": "John Doe",
            "email": "john-doe@kyzo.com",
            "password": "JohnDoe1234",
            "grade": 6,
            "role": UserRole.STUDENT
        },
        {
            "name": "Joe Bloggs",
            "email": "joe-bloggs@kyzo.com",
            "password": "JoeBloggs1234",
            "grade": 6,
            "role": UserRole.TEACHER
        },
        {
            "name": "John Smith",
            "email": "john-smith@kyzo.com",
            "password": "JohnSmith1234",
            "grade": 6,
            "role": UserRole.ADMIN
        }
    ]

    # --- Academic Subjects ---
    SUBJECTS = [
        {
            "name": "Deutsch"
        },
        {
            "name": "Geschichte"
        }
    ]

    # --- Educational Topics ---
    TOPICS = [
        {
            "subject_id": 1,
            "name": "Personen Beschreibung",
            "grade_expected": 6
        },
        {
            "subject_id": 1,
            "name": "Kommasetzung",
            "grade_expected": 6
        },
        {
            "subject_id": 2,
            "name": "Altes Ägypten",
            "grade_expected": 6
        },
        {
            "subject_id": 2,
            "name": "Antikes Griechenland",
            "grade_expected": 6
        },
    ]

    # --- Raw Content for Question Generation ---
    QUESTION_INPUTS = [
        {
            "user_id": 2,
            "subject_id": 1,
            "topic_id": 1,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Personenbeschreibung\r\nArbeitsblätter mit Übungen und Aufgaben zur Personenbeschreibung für Deutsch in der 5. Klasse an Gymnasium & Realschule - zum einfachen Herunterladen und Ausdrucken als PDF - mit Lösungen.\r\n\r\nTipps zur Erstellung einer Personenbeschreibung:\r\nWas ist der Zweck deiner Personenbeschreibung?\r\nHandelt es sich um eine polizeiliche Vermisstenanzeige oder möchtest du bei einem Ratespiel eine Person beschreiben?\r\n\r\nWas interessiert den Leser? Welche Fachbegriffe kennt er oder sie?\r\n\r\nSammle zuerst Oberbegriffe, zu denen du nähere Informationen geben möchtest.\r\nErgänze dann stichpunktartig passende Begriffe, zum Beispiel zu Name, Alter, Geschlecht, Größe, Figur, Gesicht, Frisur, Körperhaltung, Gang, Bekleidung, Schuhe sowie Schmuck oder Accessoires.\r\n\r\nBenenne interessante Fakten: Hat die Person besondere Merkmale oder trägt sie auffälligen Schmuck?\r\n\r\nWortwahl:\r\nVerwende treffende Adjektive und Fachbegriffe. Nutze zusammengesetzte Wörter, um dich kurz und präzise auszudrücken.\r\nVerwende nur sachliche Beschreibungen.\r\n\r\nSprachliche Gestaltung:\r\nVermeide Wortwiederholungen, verwende unterschiedliche Satzanfänge und abwechslungsreiche Verben.\r\nSchreibe dann deine Stichpunkte als flüssigen, kurzen Text im Präsens auf.\r\n\r\nWie ist eine Personenbeschreibung aufgebaut?\r\nSo wird eine Personenbeschreibung in der Regel strukturiert:\r\n\r\nEine kurze Einleitung nennt ggf. Name, Geschlecht, Alter, Größe und Gestalt der Person.\r\nEine Vermisstenanzeige sollte auch Zeit und Ort des letzten bekannten Aufenthalts der Person enthalten.\r\nIm Hauptteil werden die Informationen zu den einzelnen Kategorien gegeben.\r\nGehe dabei systematisch vor – z. B. von Kopf bis Fuß oder vom Großen zum Kleinen.\r\nVermeide es, zwischen den Kategorien hin und her zu springen.\r\nHebe besondere Kennzeichen, die eine eindeutige Identifizierung ermöglichen, deutlich hervor.\r\n\r\nRunde den Text mit einem Schlusssatz ab.\r\nGehe z. B. noch einmal auf den Gesamteindruck ein, den die Person auf dich macht.\r\nDie Leser einer Vermisstenanzeige sollen freundlich zur Mithilfe bei der Suche aufgefordert werden.\r\nDeshalb sind hier Kontaktmöglichkeiten dringend erforderlich."
            }
        },
        {
            "user_id": 3,
            "subject_id": 1,
            "topic_id": 1,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Eine Person beschreiben\r\nDie Personenbeschreibung\r\nEine Beschreibung ist ein sachlicher Text, in dem du Wege, Personen, Tiere oder Vorgänge anschaulich darstellst.\r\n Anschaulich heißt dabei, dass sich andere, die den beschriebenen Gegenstand usw. nicht kennen, eine genaue Vorstellung davon machen können.\r\n\r\nWenn du eine Person beschreiben möchtest, musst du dir die Person zuerst genau anschauen.\r\n\r\nEine Person beschreiben\r\nDeine Personenbeschreibung muss eine klare Struktur aufweisen.\r\nLege dir zunächst einen Stichwortzettel an, auf dem du dir Notizen zu allen Punkten deiner Beschreibung machst.\r\n\r\nGliedere deine Beschreibung vom Großen zum Kleinen, werde also immer genauer!\r\n\r\nTeile der Personenbeschreibung\r\nDein Stichwortzettel sollte Notizen zu folgenden Kennzeichen haben:\r\n\r\nAllgemeine Angaben zur Person:\r\n\r\nName\r\nGeschlecht\r\nAlter (ggf. geschätzt)\r\nAussehen der Person:\r\n\r\nGestalt:\r\nGröße, Körperstatur, Hautfarbe, Gliedmaßen (Arme, Hände, Beine, Füße), Haltung, Gang\r\nKopf und Gesicht:\r\nKopfform, Haare, Stirn, Augen, Nase, Mund und Lippen, Zähne, Kinn, Hals\r\nKleidung:\r\nArt der Kleidung, Stoff, Farbe, Schnitt, Schuhe\r\nBewegung/Körperhaltung:federnd, schleppend, langsam, schnell, aufrecht, gebeugt\r\n\r\nBesonderheiten:\r\nNarben, Piercings, Schmuck\r\nNicht immer kannst du zu allen Aspekten etwas sagen!\r\n\r\nAufbau einer Personenbeschreibung\r\nDie Personenbeschreibung wird in Einleitung, Hauptteil und Schluss unterteilt.\r\n\r\nIn der Einleitung machst du Angaben zu den wichtigsten Merkmalen der Person.\r\n\r\nIm Hauptteil formulierst du nähere Informationen zum Aussehen der Person. Hierbei ist es wichtig, dass du auf eine logische Reihenfolge achtest. Beispielsweise kannst du bei der Beschreibung von Kopf bis Fuß vorgehen.\r\n\r\nZum Schluss machst du Angaben zum Gesamteindruck der Person (Wirkung der Person).\r\n\r\nDie Personenbeschreibung bezieht sich nur auf die äußeren und somit sichtbaren Merkmale der Person.\r\n\r\nStil der Personenbeschreibung\r\nBei der Personenbeschreibung musst du folgende Dinge beachten:\r\n\r\nAchte auf eine sinnvolle Reihenfolge, also beschreibe z. B. von oben nach unten!\r\nVerwende anschauliche Adjektive, um die Person genau zu beschreiben!\r\nDas Tempus der Personenbeschreibung ist das Präsens!\r\nSchreibe in der Er-/Sie-Form!\r\n\r\nBleibe sachlich und vermeide persönliche Empfindungen!\r\nFormulierungshilfen\r\nPräge dir folgende Formulierungen für deine Personenbeschreibung ein. So fällt es dir leichter, die Personenbeschreibung abwechslungsreich zu verfassen:\r\n\r\nauffallend an ihm/ihr ist …\r\n… ist deutlich zu erkennen\r\n… steht ihm gut\r\n… sind nicht zu übersehen\r\nzeichnet sich durch … aus\r\n… treten besonders hervor\r\nauffälliges Merkmal ist …\r\nhervorstechendes Kennzeichen ist …"
            }
        },
        {
            "user_id": 1,
            "subject_id": 1,
            "topic_id": 2,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Drei Tipps für ein Dauerthema im Deutschunterricht – damit die Grundlagen für die späteren Klassenstufen richtig gelegt werden.\r\n\r\nFragt man ältere Lernende oder Erwachsene, wie sie Kommas setzen, dann kommt häufig als Antwort „nach Gefühl“. Tatsächlich ist es wichtig, den Schülerinnen und Schülern ein Gespür für Satzkonstruktionen, für Anfang und Ende von Teilsätzen und auch für Signale, die eine Kommasetzung ankündigen, zu vermitteln – aber natürlich müssen sie trotzdem die Kommaregeln kennen.\r\n\r\nIn Klasse 5 und 6 spielen zunächst nur die Kommasetzung bei Aufzählungen, in Satzgefügen und Satzverbindungen eine Rolle. Im Download finden Sie noch einmal alle Regeln der Kommasetzung übersichtlich und schülergerecht anhand von Eselsbrücken auf einer Seite zusammengestellt.\r\n\r\nDas finite Verb als Dreh- und Angelpunkt\r\nWenn Kommas ausschließlich „nach Gefühl“ gesetzt werden, kommt es – vor allem wenn ein Satz zum Beispiel durch verschiedene Adverbialbestimmungen eine gewisse Länge hat –, häufig dazu, dass zu viele und falsche Kommas gesetzt werden. Stattdessen sollten Sie Ihren Schülerinnen und Schülern vermitteln, dass das finite Verb Dreh- und Angelpunkt für die Satzstruktur und damit für die Kommasetzung ist. Mit folgenden Beispielsätzen können Sie die Abhängigkeit der Kommasetzung von den finiten Verben bewusst machen: Die Spieler sind schneller gelaufen als wir (eine finite Verbform → kein Komma). Die Spieler sind schneller gelaufen, als wir dachten. (zwei finite Verbformen → ein Komma). Ab Klasse 5 ist es deswegen so wichtig, immer wieder das Bestimmen finiter Verben in komplexen Sätzen zu üben. Dafür finden Sie im Download eine entsprechende Arbeitstechnik.\r\n\r\nSignale für die Kommasetzung\r\nDas Bestimmen von Haupt- und Nebensätzen und die Kommasetzung ist gar kein so unbeliebtes Thema in den unteren Klassen, solange die Sätze vorgegeben sind. Schwierig wird es für die Schülerinnen und Schüler, wenn sie eigene Sätze formulieren und dort die Kommas setzen müssen. Hier ist es wichtig, dass sie nach und nach beim Schreiben eine gewisse Intuition entwickeln, wann ein Komma gesetzt werden muss. Als Faustregel können Sie ihnen vermitteln, dass ein Komma gesetzt werden muss, wenn zwei finite Verbformen direkt aufeinander folgen (Beispiel: Als das Futter endlich kam, freuten sich die Tiere.). Außerdem sollten sich die Schülerinnen und Schüler an sogenannten Signalwörtern für die Kommasetzung orientieren, also zum Beispiel an Konjunktionen und Relativpronomen.\r\n\r\nZusammengesetzte Sätze bilden\r\nIn Klasse 5 und 6 schreiben viele Schülerinnen und Schüler noch in einfachen Hauptsätzen, sodass es wichtig ist, zunächst das sinnvolle Verknüpfen von Hauptsätzen zu zusammengesetzten Sätzen zu üben und dort natürlich dann auch die Kommas zu setzen. Beim Berichten und Beschreiben – ein klassisches Aufsatzthema in dieser Altersstufe – ist es notwendig, unter anderem kausale und temporale Zusammenhänge darzustellen.\r\n\r\nHier können Sie funktional das Verknüpfen von Sätzen und die Kommasetzung schrittweise üben. Im Download finden Sie dazu ein Arbeitsblatt zum Bilden zusammengesetzter Sätze und der Kommasetzung, Ausgangspunkt ist eine Aufgabe im Arbeitsheft Deutsch kompetent Klasse 6."
            }
        },
        {
            "user_id": 3,
            "subject_id": 1,
            "topic_id": 2,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Kommasetzung\r\nArbeitsblätter zum Thema Kommasetzung für Deutsch am Gymnasium und in der Realschule - zum einfachen Herunterladen als PDF und Ausdrucken\r\n\r\nWann setze ich ein Komma richtig ein?\r\nEin Komma trennt Wörter, Wortgruppen oder Teilsätze vom übrigen Satz ab. Dadurch werden Sätze nach grammatischen Regeln gegliedert. Ein Komma ist notwendig, um den Satz klar und verständlich zu machen. Ohne korrekte Zeichensetzung können Missverständnisse entstehen. Zudem zeigt das Komma an, wo kurze Pausen beim Lesen oder Sprechen sinnvoll sind.\r\n\r\nWie setze ich ein Komma bei Aufzählungen?\r\nEin Komma muss bei Aufzählungen von Nomen oder Wortgruppen gesetzt werden.\r\n\r\nAchtung: Werden die Aufzählungen durch und, oder, sowie, sowohl … als auch, entweder … oder, weder … noch verbunden, wird kein Komma gesetzt.\r\n\r\nBeispiele:\r\n\r\nIm Blumenbeet stehen Tulpen, Geranien, Chrysanthemen und Rosen dicht an dicht.\r\nIch mag Fußball spielen, Bücher lesen, Comics zeichnen.\r\n \r\nEine Aufzählung von Adjektiven wird nur dann durch ein Komma getrennt, wenn die Adjektive gleichrangig sind. Gleichrangige Adjektive können durch und verbunden werden, ohne den Sinn des Satzes zu verändern. Ist ein Adjektiv jedoch bereits fest mit einem Nomen verbunden (z. B. die italienische Küche), und wird diese Verbindung durch ein weiteres Adjektiv näher bestimmt, so wird kein Komma gesetzt.\r\n\r\nBeispiele:\r\n\r\nDie Halle ist mit roten, grünen sowie blauen Luftballons geschmückt. (gleichrangig)\r\nIm Urlaub habe ich die gute italienische Küche genossen. (Ergänzung einer festen Verbindung)\r\n \r\nEine Aufzählung von zwei oder mehr Hauptsätzen (Satzreihen) wird durch ein Komma getrennt. Hauptsätze können eigenständig stehen, werden jedoch durch ein Komma verbunden, wenn sie in einem Satz zusammengefasst sind.\r\n\r\nBeispiel:\r\n\r\nEr isst gern Pizza, sie mag lieber Nudeln.\r\nWie setze ich das Komma zwischen Hauptsatz und Nebensatz?\r\nDas Komma trennt einen untergeordneten Nebensatz vom Hauptsatz ab. Der Nebensatz kann dabei vorangestellt, eingeschoben oder nachgestellt sein.\r\n\r\nZur Erinnerung: Ein Nebensatz kann nie alleine stehen. Das finite Verb steht in einem Nebensatz immer am Ende.\r\n\r\nKonjunktionalsätze\r\nEin Konjunktionalsatz ist ein Nebensatz, der mit einer Konjunktion beginnt. Typische Konjunktionen sind z. B.:\r\nals, da, wenn, falls, weil, (so) dass, indem, während, obwohl, damit.\r\n\r\nBeispiele:\r\n\r\nTina möchte, falls ihr Auto heute anspringt, zum Einkaufen nach Augsburg fahren.\r\nIch glaube nicht, dass die Batterie ihres Autos noch geladen ist.\r\nRelativsätze\r\nEin Relativsatz ist ein Nebensatz, der mit einem Relativpronomen beginnt. Das Relativpronomen bezieht sich auf ein Nomen oder Pronomen im Hauptsatz: der, die, das, welches (auch in deklinierter Form: den, dem, welchen usw.). Es kann auch hinter einer Präposition stehen.\r\n\r\nBeispiele:\r\n\r\nFrau Braun kauft den Koffer, den sie im Schaufenster gesehen hat.\r\nEndlich trifft die Freundin ein, auf die sie schon im Café gewartet hat.\r\nIndirekte Fragesätze\r\nEin indirekter Fragesatz wird mit einem Fragewort eingeleitet.\r\n\r\nBeispiel:\r\n\r\nIch weiß wirklich nicht, woher dieser Dreck auf der Straße kommt.\r\nInfinitivgruppen\r\nEine Infinitivgruppe (zu + Infinitiv) muss mit einem Komma abgetrennt werden, wenn sie durch Hinweiswörter wie als, (an)statt, außer, ohne, statt, um eingeleitet wird. Auch bei den Wörtern es, darauf, daran trennt man die Infinitivgruppe mit einem Komma ab.\r\n\r\nBeispiele:\r\n\r\nDie Maus lief durch das Feld, ohne auf den Raubvogel über ihr zu achten.\r\nIch freue mich darauf, euch morgen auf der Party zu treffen.\r\nPartizipgruppen\r\nEine Partizipgruppe muss mit einem Komma abgetrennt werden, wenn sie das Subjekt näher beschreibt oder erläutert. Das gilt auch, wenn die Gruppe durch ein Signalwort wie so eingeleitet wird. Steht die Partizipgruppe jedoch unmittelbar hinter dem Prädikat, ist kein Komma erforderlich.\r\n\r\nBeispiele:\r\n\r\nDie Körner suchend, so lief die Maus durch das Feld.\r\nDer Raubvogel, eine Maus erspähend, steht über dem Feld.\r\nDer Raubvogel steht über dem Feld, eine Maus erspähend.\r\nWie setze ich das Komma bei Zusätzen?\r\nEin Komma trennt nachgestellte Zusätze oder Erläuterungen vom übrigen Satz ab. Nachgestellte Erläuterungen werden häufig mit folgenden Wörtern eingeleitet: also, und zwar, vor allem, sogar, zum Beispiel, aber, insbesondere, das heißt, nämlich.\r\n\r\nHinweis: Eine Beifügung des Nomens (Apposition) steht immer im gleichen Fall wie das Nomen, auf das sie sich bezieht.\r\n\r\nBeispiele:\r\n\r\nIch esse gerne Nudeln, vor allem Makkaroni.\r\nDer große Junge dort, unser Nachbar, übt jeden Tag Schlagzeug.\r\nWie setze ich das Komma bei Anrede, Ausruf oder einer Bekräftigung?\r\nEine Anrede, ein Ausruf oder eine Bekräftigung werden mit einem Komma vom übrigen Satz abgetrennt. Diese Elemente stehen oft außerhalb des Satzgefüges und dienen der Betonung, Hervorhebung oder der direkten Ansprache.\r\n\r\nBeispiele:\r\n\r\nHerr Meier, können Sie sich bitte darum kümmern? (Anrede)\r\nDie Spinne ist riesig, igitt! (Ausruf)\r\nStimmt, das sehe ich genauso. (Bekräftigung)\r\nHinweis: Solche abgetrennten Satzteile werden meist betont gelesen oder gesprochen und stehen in der Regel am Satzanfang oder Satzende.\r\n\r\nWie setze ich Kommas bei der direkten und indirekten Rede?\r\nWie setze ich Kommas bei der direkten und indirekten Rede?\r\n\r\nEin Komma trennt die wörtliche Rede vom begleitenden Satz (Redebegleitsatz) ab. Dabei gelten folgende Regeln:\r\n\r\nDirekte Rede:\r\n\r\nSteht der Redebegleitsatz vor der wörtlichen Rede, folgt das Komma nach dem Redebegleitsatz.\r\nSteht der Redebegleitsatz nach der wörtlichen Rede, wird die wörtliche Rede durch ein Komma (innerhalb der Anführungszeichen) davon getrennt.\r\nWird der Redebegleitsatz in die wörtliche Rede eingeschoben, wird dieser durch Kommas von der wörtlichen Rede abgetrennt.\r\nBeispiele:\r\n\r\nSonja fragt: „Wann können wir dieses Jahr den Urlaub einplanen?“\r\n„Wann können wir dieses Jahr den Urlaub einplanen?“, fragt Sonja.\r\n„Wann“, fragt Sonja, „können wir dieses Jahr den Urlaub einplanen?“\r\n\r\nIndirekte Rede:\r\nIn der indirekten Rede wird ebenfalls ein Komma gesetzt, um den einleitenden Satz vom Nebensatz abzutrennen. Der Nebensatz beginnt meist mit einer Konjunktion wie dass, ob oder einem Fragewort.\r\n\r\nBeispiel:\r\n\r\nSonja fragt, wann sie dieses Jahr den Urlaub einplanen können.\r\n\r\nHinweis:\r\n\r\nIn der direkten Rede steht das Satzschlusszeichen (z. B. Punkt, Fragezeichen, Ausrufezeichen) innerhalb der Anführungszeichen.\r\nEin Doppelpunkt leitet die wörtliche Rede ein, wenn der Redebegleitsatz davor steht."
            }
        },
        {
            "user_id": 3,
            "subject_id": 2,
            "topic_id": 3,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Das alte Ägypten\r\nWann lebten die Ägypter?\r\nDie Ägypter lebten von ca. 3000 v. Chr. bis 30 v. Chr.\r\nÄgypten galt als „Geschenk des Nils“, da es in der Wüstenlandschaft außer im Niltal keine guten Lebensbedingungen gab.\r\n\r\nWie war die ägyptische Gesellschaft aufgebaut?\r\nAn erster Stelle stand der Pharao – er war uneingeschränkter Herrscher über Ägypten.\r\nEr galt als Vermittler zwischen Göttern und Menschen.\r\n\r\nDanach folgte der Wesir, der als Stellvertreter des Pharaos diente.\r\nDer Wesir beriet den Pharao und erstattete Bericht.\r\n\r\nAuf der nächsten Stufe folgten die Beamten und Priester, auch sie berichteten dem Wesir oder Pharao.\r\n\r\nGanz unten in der Hierarchie standen die Bauern – die größte Bevölkerungsgruppe.\r\nSie bestellten das vom Pharao gepachtete Land.\r\nDer Ertrag wurde in Speicher gebracht – zur Sicherung und als Bezahlung der höhergestellten Personen.\r\nWas sind Hieroglyphen?\r\nDie Hieroglyphen sind die Schriftzeichen der alten Ägypter.\r\nSie nutzten sie, um sich zu verständigen, indem sie Dinge aufschrieben, zum Beispiel Listen über Vorräte.\r\n\r\nWarum wird Ägypten als „Hochkultur“ bezeichnet?\r\nDie Ägypter hatten schon früh eine eigene Schrift (Hieroglyphen) und eine Staatsstruktur mit einem Verwaltungsapparat.\r\nDeshalb wird Ägypten als „Hochkultur“ bezeichnet.\r\n\r\nWie wohnten die Menschen im alten Ägypten?\r\nDie Wohnhäuser waren aus Bruchstein, Lehmziegeln, Holz und Schilfmatten gebaut.\r\nMeist waren sie einstöckig und hatten ein Flachdach.\r\nDer Herd befand sich meistens im Hof oder in einer nicht überdachten Küche.\r\nAnsonsten gab es Stühle, kleine Tische, Betten und Truhen.\r\n\r\nWann endet die Zeit der Pharaonen und wann die Zeit des alten Ägypten?\r\nDie Zeit der ägyptischen Pharaonen endete mit der Niederlage gegen Alexander den Großen.\r\n\r\nDie Zeit des Alten Ägypten endete mit der Niederlage der griechischen Pharaonen gegen Rom.\r\nÄgypten wurde eine römische Provinz."
            }
        },
        {
            "user_id": 3,
            "subject_id": 2,
            "topic_id": 4,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Das antike Griechenland hat die Entwicklung der europäischen Zivilisation maßgeblich mitgeprägt. Es umfasst im Kern den Zeitraum von ca. 800 v. Chr. bis zur Einbeziehung des letzten der hellenistischen Reiche 30 v. Chr. ins Römische Reich. Kulturgeschichtlich wirkten diverse Erscheinungsformen, Entwicklungen und Hervorbringungen aber weit darüber hinaus und teils bis in die Gegenwart nach. Die antike griechische Geschichte wird dabei traditionell unterteilt in die drei Epochen Archaik, Klassik und Hellenismus.\r\n\r\nDie archaische Epoche Griechenlands folgte dabei dem Zerfall der mykenischen Kultur und den sogenannten „dunklen Jahrhunderten“ (von ca. 1050 bis ca. 800 v. Chr.). Bald nach der Entstehung des griechischen Alphabets wurden bereits grundlegende Werke der abendländischen Dichtkunst, wie vor allem die Ilias und die Odyssee, schriftlich festgehalten. Im Zeitraum von 800 bis 500 v. Chr. etablierte sich die Polis als Staatsform, und es kam zur Gründung vieler griechischer Kolonien im Mittelmeerraum und am Schwarzen Meer. In der Archaik entstanden zudem erste Formen friedlichen sportlichen Wettstreits für alle Hellenen, wie die Olympischen Spiele.\r\n\r\nIn der folgenden klassischen Periode (ca. 480–336 v. Chr.), die unter anderem die Selbstbehauptung der Griechen in den Perserkriegen sowie die Entwicklung und Ausgestaltung der attischen Demokratie, aber auch zerstörerische Kriege griechischer Poleis untereinander wie den Peloponnesischen Krieg beinhaltete, kam es verschiedentlich zu einer politischen, wirtschaftlichen und kulturellen Entfaltung, die ihresgleichen in vormodernen Zeiten sucht und die ein Fundament für das Abendland legte. Prägend war dabei vor allem Athen, das im Mittelpunkt der schriftlichen Überlieferung zu dieser Zeit steht. Zu den exemplarischen Leistungen der antiken griechischen Kultur zählen:\r\n\r\narchitektonische Monumente wie auf der Athener Akropolis,\r\nbedeutende Skulpturen, die zeitübergreifend Maßstäbe setzten,\r\nBlüte der Philosophie, deren bedeutendste Vertreter Platon und Aristoteles in dieser Zeit wirkten\r\nfundamentale und überdauernde Begriffsbildung auch im Bereich Politik, wie zum Beispiel Demokratie, Aristokratie oder Oligarchie,\r\ndie Entstehung des Dramas, namentlich der Werke von Sophokles, Aischylos, Euripides und Aristophanes,\r\ndie Begründung der abendländischen Geschichtsschreibung durch Herodot und Thukydides mit bedeutender Nachwirkung,\r\nmaßgebliche Erkenntnisse auf dem Gebiet der Mathematik und Physik.\r\nMit dem makedonischen König Alexander dem Großen begann die letzte Epoche der eigenständigen griechischen Geschichte, der Hellenismus (ca. 336–27 v. Chr.). Diese Zeit war durch das Ende der Sonderrolle Athens, die Gründung zahlreicher neuer Poleis und die Verbreitung griechischer Sprache und Kultur bis nach Vorderindien, durch die gegenseitige Durchdrindung von östlicher und westlicher Zivilisation und Religion sowie insbesondere durch die Etablierung von Großreichen, die von makedonischen Königen beherrscht wurden, gekennzeichnet. Auch der Hellenismus brachte bedeutende intellektuelle und künstlerische Leistungen hervor; so wirkten damals Denker wie Archimedes und Eratosthenes, die bis heute wirkenden Denktraditionen der Stoa und des Epikureismus wurden begründet und monumentale Kunstwerke wie der Pergamonaltar geschaffen.\r\n\r\nAb 200 v. Chr. geriet der östliche Mittelmeerraum in einem gut 150 Jahre dauernden Prozess schrittweise unter römische Herrschaft und wurde schließlich Teil des Imperium Romanum, zuletzt 30 v. Chr. das Reich der Ptolemäer. 27 v. Chr. wurde der größere Teil Griechenlands zur römischen Provinz Achaea. Damit endete die politische Selbstständigkeit der griechischen Welt, kulturell war der östliche Mittelmeerraum aber bis in die endende Spätantike und teils darüber hinaus stark griechisch geprägt.\r\n\r\nVorbemerkungen\r\nDie folgenden Einteilungen des antiken Griechenlands folgen geltenden Konventionen, die sich wissenschaftsgeschichtlich entwickelt haben. In der deutschsprachigen Alten Geschichte prägten Helmut Berve (1931) und Alfred Heuß (1946) den Blick auf den frühesten Abschnitt griechischer Geschichte als archaische Zeit.[1] Raimund Schulz und Uwe Walter (2022) arbeiten in ihrem Handbuch zur griechischen Geschichte noch mit der konventionellen Einteilung in archaische und klassische Zeit, schlagen jedoch auch neue Zäsuren vor, indem sie – orientiert an Alfred Heuß – über den Zeitraum von um 550 bis 400 v. Chr. als „Die Griechen machen große Politik“ sprechen.[2] Die Perspektive unserer antiken Quellen legt die gängige Epocheneinteilung einerseits nahe; andererseits funktioniert die Epocheneinteilung – durch die Zielsetzung des jeweiligen antiken Geschichtswerkes und der damit einhergehenden Verengung – insbesondere für die bedeutenden griechischen Akteure des Ägäisraumes und nicht zwangsläufig für die Griechen im westlichen Mittelmeerraum oder im Schwarzmeergebiet sowie weniger bedeutende griechische Städte und Gemeinschaften."
            }
        },
        {
            "user_id": 1,
            "subject_id": 2,
            "topic_id": 4,
            "grade": 6,
            "input_type": InputType.MANUAL,
            "raw_input": {
                "content": "Die griechische Antike gilt als Wiege der europäischen Zivilisation. Viele der Errungenschaften aus dieser Zeit haben bis heute Bestand.\r\n\r\nDie Geschichte des antiken Griechenlands beginnt etwa 800 vor Christus mit der Gründung verschiedener Poleis. Das sind kleine Stadtstaaten, in denen sich die Bürger organisierten. Das altgriechische Wort \"Polis\" bedeutet wörtlich \"Stadt\". Daher stammt auch der Begriff Politik – zu deutsch: die Kunst der Staatsverwaltung.\r\n\r\nDie gemeinsame Sprache aller Stadtstaaten war griechisch. Ab etwa 800 vor Christus entwickelte sich auch die griechische Literatur. Zu den wichtigsten Werken gehören die Helden-Erzählungen \"Ilias\", die vom Kampf um Troja berichten, und die \"Irrfahrten des Odysseus\" vom berühmten Dichter Homer.\r\n\r\nAthen wurde zum geistigen Zentrum Griechenlands. Hier lebten große Philosophen wie Platon und sein Schüler Aristoteles, die sich viele Gedanken machten: Was ist der Ursprung der Welt? Wie hängt alles miteinander zusammen?\r\n\r\nIn Olympia fanden seit 776 vor Christus alle vier Jahre Wettkämpfe statt. Die besten Sportler des Landes traten an, um sich bei Wettkämpfen zu messen – in vielen Disziplinen wie Laufen, Boxen oder Pferderennen.\r\n\r\nAb 500 vor Christus entstand in Athen die Demokratie. In Volksversammlungen entschieden etwa 50.000 freie Bürger – Frauen und Sklaven ausgenommen – über Rechtsurteile oder Verbannungen.\r\n\r\nDas antike Griechenland endete um 30 vor Christus, nachdem das Römische Reich fast alle griechischen Gebiete in Besitz genommen hatte. Aber die Errungenschaften dieser Zeit prägen bis heute unser Leben."
            }
        }
    ]
