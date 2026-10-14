#!/bin/sh
# Renombra la organizacion id=1 de Grafana a Smartek de forma idempotente.

#Mediante set -u hacemos que el script falle si alguna variable no esta definida
set -u


#Definimos la URL y el nombre de la organizacion a renombrar
GRAFANA_URL="${GRAFANA_URL}"
ORG_NAME="${GRAFANA_ORG_NAME}"

#Compruebo que las variables no esten vacias mediante -z
# Mediante "$" devuelve el valor de la variable
# El operador || funciona como {or}
# Si se comple el condicional mostrara mediante el echo el error
if [ -z "${GF_SECURITY_ADMIN_USER}" ] || [ -z "${GF_SECURITY_ADMIN_PASSWORD}" ]; then
  echo "ERROR: faltan GF_SECURITY_ADMIN_USER / GF_SECURITY_ADMIN_PASSWORD" >&2
  exit 1
fi

#--silent	Oculta la barra de progreso y los mensajes habituales de transferencia.
#--show-error	Permite mostrar el error aunque se use --silent.
#--max-time 5	Limita cada petición a un máximo de 5 segundos.
#--retry 60	Permite hasta 60 reintentos cuando la petición falla.
#--retry-delay 5	Espera 5 segundos entre reintentos.
#--retry-all-errors	Solicita reintentar ante cualquier tipo de error.
#--output /dev/null	Mandamos la respuesta a un "agujero negro" para que no se muestre en pantalla, solo nos interea saber si funciona
# Todo esto lo utilizamos para ver si podemos conectarnos y transferir datos

echo "-> esperando a Grafana en ${GRAFANA_URL} ..."
if ! curl --silent --show-error --max-time 5 --retry 60 --retry-delay 5 --retry-all-errors --output /dev/null "${GRAFANA_URL}/api/health"; then
  echo "ERROR: Grafana no responde tras los reintentos" >&2
  exit 1
fi

# Guardamos el comando en la varaible BODY
# Utilizamod curl -u, para autentificacion
# Enviamos los parametros del .env a la URL DE GRANA /api/org

BODY="$(curl  --silent --show-error --max-time 10 -u "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" "${GRAFANA_URL}/api/org")" || exit 1

# Comprobamos de la variable Body /name es el mismo que la variable de nuestro entornor
# EN caso de ser asi mostramos un mensaje que todo ha sido correcto
# ;; terminamos el case
case "${BODY}" in
  *"\"name\":\"${ORG_NAME}\""*)
    echo "OK: la organizacion ya es '${ORG_NAME}', nada que hacer."
    exit 0
    ;;
esac

echo "-> renombrando organizacion a '${ORG_NAME}' ..."
# En este momento realizamos el cambio 
# \ la barra invertida al final nos permite continuar en la siguiente linea
# if !, comprueba si el comando curl falla, en caso de que falle mostramos un mensaje de error y salimos con exit 1
# - X PUT, para indicar que vamos a modificar un recurso
# -H, para explicar el formato que enviamos, en este caso JSON
# -d, para indicar los datos que enviamos, en este caso el nombre de la organizacion
# Si no ha devuelto error, mostramos un mensaje de que todo ha ido bien
if ! curl --silent --show-error --max-time 10 --retry 5 --retry-delay 3 --retry-all-errors \
    -u "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" \
    -X PUT -H "Content-Type: application/json" \
    -d "{\"name\":\"${ORG_NAME}\"}" \
    "${GRAFANA_URL}/api/org"; then
  echo "ERROR: no se pudo renombrar (revisa las credenciales de admin)" >&2
  exit 1
fi
echo "OK: organizacion renombrada a '${ORG_NAME}'."
