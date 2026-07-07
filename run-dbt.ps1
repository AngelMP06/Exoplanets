# run_dbt.ps1
# Carga las variables de entorno desde .env y luego ejecuta dbt con los argumentos que le pases.
#
# Uso:
#   .\run_dbt.ps1 debug
#   .\run_dbt.ps1 run
#   .\run_dbt.ps1 run --select stg_planets
#
# Requisito: este script asume que .env está en la misma carpeta donde lo ejecutas
# (la raíz de tu proyecto dbt). Si tu .env está en otro lugar, ajusta $envPath abajo.

$envPath = ".env"

if (-Not (Test-Path $envPath)) {
    Write-Host "No se encontró $envPath en la carpeta actual. Ejecuta este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

Write-Host "Cargando variables desde $envPath..." -ForegroundColor Cyan

Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()

    # Ignorar líneas vacías y comentarios
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }

    # Separar en NOMBRE=VALOR (solo por el primer "=")
    $parts = $line -split "=", 2
    if ($parts.Length -eq 2) {
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()

        # Quitar comillas si el valor viene entre comillas simples o dobles
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            $value = $value.Substring(1, $value.Length - 2)
        } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        Set-Item -Path "env:$name" -Value $value
    }
}

Write-Host "Variables cargadas. Ejecutando: dbt $($args -join ' ')" -ForegroundColor Green

# Ejecuta dbt pasando todos los argumentos recibidos por el script
dbt @args