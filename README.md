# Zadanie 1: Parsowanie JSON
### W pliku "ogloszenia.json" znajduje się 656 ogłoszeń z serwisu aukcyjnego. Niektóre z nich nie posiadają atrybutu ceny ("offerPrice") oraz atrybutu zdjęć ("offerPics").  Twoim zadaniem będzie pozbycie się wadliwych ogłoszeń bez ceny, te bez zdjęć mogą zostać, jednak oba przypadki należy uwzględnić w logach. Do tego celu stwórz nowe klasy wyjątków, oraz funkcję walidującą poszczególne oferty, która będzie je rzucać.
 
# Zadanie 2: Ponawianie przy wystąpięniu błędu. 
### Poniższy kod symuluje występowanie dwóch błędów podczas połączeń - timeout oraz bad gateway. Korzystając z niego wywołaj ```sim_get_response()``` i zbuduj następującą strukturę obsługi wyjątków: podczas pojawienia się timeout'u, kontynuuj próbę nawiązania połączenia do 10 razy (z sekundowymi przerwami pomiędzy). Podczas niepowodzenia, lub podczas pojawienia się błędu 502 - zerwij połączenie, poczekaj trzy sekundy i spróbuj połączyć się ponownie (do 3 razy). Jeśli wszystko zawiedzie - możesz użyć wyjątku ```SimConnectionFailure```.
```
import random, logging, time

class SimConnectionFailure(Exception):
    """Simulates connection failure"""
    pass

class SimBadGatewayError(SimConnectionFailure):
    """Simulates HTTP 502 error."""
    pass

class SimTimeoutError(SimConnectionFailure):
    """Simulates timeout error"""
    pass

def sim_get_response():
    rand = random.random()
    if rand < 0.8:
        raise SimTimeoutError("Connection timed out.")
    if rand < 0.8:
        raise SimBadGatewayError("Bad gateway", 502)
    return 200
```
