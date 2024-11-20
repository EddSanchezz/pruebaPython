import json
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
from driver import iniciar_chrome
from config import FACEBOOK_USER, FACEBOOK_PASS

URL = "https://www.facebook.com/Google"
COOKIES_FILE = "cookies_facebook.json"

def cargar_cookies(driver, cookies_file):
    with open(cookies_file, "r") as file:
        cookies = json.load(file)
    for cookie in cookies:
        driver.add_cookie(cookie)

def traducir(texto, destino="es"):
    translator = Translator()
    try:
        return translator.translate(texto, dest=destino).text
    except Exception as e:
        print(f"Error al traducir texto: {e}")
        return texto

def quitar_emojis(texto):
    return texto.encode("ascii", "ignore").decode("ascii")

def obtener_numero(texto):
    try:
        return int(''.join(filter(str.isdigit, texto)))
    except:
        return 0

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrapear_facebook():
    driver = iniciar_chrome()
    driver.get("https://www.facebook.com/")
    
    cargar_cookies(driver, COOKIES_FILE)
    driver.refresh()
    
    driver.get(URL)
    wait = WebDriverWait(driver, 15)
    
    try:
        time.sleep(5)
        nombre_cuenta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))).text
        
        
        seguidores_texto = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'seguidores')]"))
        ).text
        numero_seguidores = obtener_numero(seguidores_texto)
        
        seguidos_texto = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'seguidos')]"))
        ).text
        numero_seguidos = obtener_numero(seguidos_texto)
        
        
        descripcion_element = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Descripción']")
        descripcion = traducir(descripcion_element.text) if descripcion_element else "N/A"
        
    except Exception as e:
        print(f"Error: Elementos de la cuenta no cargaron a tiempo: {e}")
        nombre_cuenta = numero_seguidores = numero_seguidos = descripcion = "N/A"
    except Exception as e:
        print(f"Error al localizar elementos de la cuenta: {e}")
        nombre_cuenta = numero_seguidores = numero_seguidos = descripcion = "N/A"
    
    with open("Cuentas.csv", mode="w", newline="", encoding="utf-8") as cuentas_file:
        writer = csv.writer(cuentas_file)
        writer.writerow(["nombre_cuenta", "numero_publicaciones", "numero_seguidores", "numero_seguidos", "descripcion"])
        writer.writerow([nombre_cuenta, "N/A", numero_seguidores, numero_seguidos, quitar_emojis(descripcion)])
    
    publicaciones = []
    try:
        time.sleep(5)  
        posts = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='article']")))
        
        for post in posts:
            try:
                
                fecha_texto = post.find_element(By.CSS_SELECTOR, "span[class*='timestamp']").get_attribute("title")
                fecha_publicacion = datetime.strptime(fecha_texto, "%d de %B de %Y")
                
                if fecha_publicacion < datetime(2024, 11, 1):
                    continue
                
                id_publicacion = post.get_attribute("id") or "N/A"
                
                descripcion_element = post.find_element(By.CSS_SELECTOR, "div[data-ad-preview='message']")
                descripcion_publicacion = traducir(descripcion_element.text) if descripcion_element else "N/A"
                
                reacciones = obtener_numero(post.find_element(By.CSS_SELECTOR, "span[aria-label*='reacción']").text)
                
                comentarios = []
                comentarios_elements = post.find_elements(By.CSS_SELECTOR, "div[data-testid='UFI2Comment/root_depth_0']")
                for comentario in comentarios_elements[:10]:
                    comentario_texto = quitar_emojis(comentario.text)
                    comentario_reacciones = obtener_numero(
                        comentario.find_element(By.CSS_SELECTOR, "span[aria-label*='reacción']").text
                    )
                    comentarios.append((comentario_texto, comentario_reacciones))
                
                publicaciones.append({
                    "Id_cuenta": nombre_cuenta,
                    "Id_publicacion": id_publicacion,
                    "Descripcion": quitar_emojis(descripcion_publicacion),
                    "Reacciones": reacciones,
                    "Comentarios": comentarios
                })
            except Exception as e:
                print(f"Error al procesar una publicación: {e}")
    except Exception as e:
        print(f"Error: Las publicaciones no cargaron a tiempo: {e}")
    
    with open("Publicaciones.csv", mode="w", newline="", encoding="utf-8") as publicaciones_file:
        writer = csv.writer(publicaciones_file)
        writer.writerow(["Id_cuenta", "Id_publicacion", "Descripcion", "Reacciones", "Comentarios", "Comentarios_reacciones"])
        for pub in publicaciones:
            for comentario in pub["Comentarios"]:
                writer.writerow([pub["Id_cuenta"], pub["Id_publicacion"], pub["Descripcion"], pub["Reacciones"], comentario[0], comentario[1]])
    
    driver.quit()

scrapear_facebook()
