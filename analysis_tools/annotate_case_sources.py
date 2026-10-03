#!/usr/bin/env python3
from pathlib import Path
import re

MARKER = "QUICKCUP DOCUMENTATION APPENDIX"
ROOTS = [Path("cases_controlled_buoyancy"), Path("cases_buoyancy"), Path("cleanproy")]

VALUE_EXPLANATIONS = {
    "application": "solver o aplicación principal que ejecuta el caso.",
    "startFrom": "define desde qué estado temporal comienza la simulación.",
    "startTime": "tiempo inicial cuando startFrom utiliza un valor explícito.",
    "endTime": "tiempo físico objetivo de la corrida; determina cuánto evoluciona la solución transitoria.",
    "deltaT": "paso de tiempo base; al disminuirlo aumenta la resolución temporal y normalmente el costo computacional.",
    "adjustTimeStep": "permite que OpenFOAM ajuste deltaT durante la corrida para respetar criterios de estabilidad.",
    "maxCo": "límite del número de Courant; acopla velocidad, tamaño de celda y paso de tiempo.",
    "maxDeltaT": "límite superior permitido para un deltaT adaptativo.",
    "writeControl": "criterio que decide cuándo se escriben resultados o diagnósticos.",
    "writeInterval": "separación entre escrituras según writeControl; determina qué tiempos quedan disponibles para análisis posterior.",
    "momentumPredictor": "activa o desactiva el predictor explícito de momento antes de las correcciones de presión.",
    "nOuterCorrectors": "número de ciclos externos PIMPLE por paso de tiempo; más ciclos refuerzan el acoplamiento a mayor costo.",
    "nCorrectors": "número de correcciones presión-velocidad dentro de cada ciclo PIMPLE.",
    "nNonOrthogonalCorrectors": "correcciones adicionales de presión asociadas a no ortogonalidad de la malla.",
    "nEnergyCorrectors": "número de correcciones de energía por paso de tiempo cuando está definido.",
    "pRefPoint": "posición usada para anclar el nivel de presión cuando la ecuación solo determina gradientes.",
    "pRefValue": "valor de presión asignado al punto de referencia; debe ser coherente con p_rgh, pRef y las BC de presión.",
    "Tsol": "temperatura solidus; fija el extremo sólido del intervalo de cambio de fase.",
    "Tliq": "temperatura liquidus; junto con Tsol define el intervalo pastoso.",
    "L": "calor latente por unidad de masa; convierte cambio de fracción de fase en fuente/sumidero de energía.",
    "Cu": "escala del término Darcy en la zona pastosa; valores mayores amortiguan más la velocidad al solidificar.",
    "q": "regularización del término Darcy que evita una singularidad cuando la fracción líquida tiende a cero.",
    "beta": "coeficiente de expansión térmica usado por la ruta de flotación que corresponda al modelo.",
    "rhoRef": "densidad de referencia utilizada por el modelo de cambio de fase/flotación cuando aplica.",
    "alpha1e": "parámetro de fracción líquida de referencia/eutéctica usado por la interpolación del cambio de fase.",
    "relax": "relajación aplicada a la actualización del modelo; valores menores amortiguan cambios entre iteraciones.",
    "convertToMeters": "factor de escala aplicado a las coordenadas de blockMesh antes de construir la geometría.",
    "internalField": "valor inicial asignado al interior del dominio antes de comenzar la integración temporal.",
    "rho0": "densidad de referencia de la formulación termofísica seleccionada.",
    "Cp": "capacidad calorífica; gobierna cuánta energía sensible se necesita para cambiar la temperatura.",
    "mu": "viscosidad dinámica; controla difusión viscosa y resistencia al movimiento.",
    "kappa": "conductividad térmica; controla transporte de calor por conducción.",
    "value": "valor indicado por el diccionario; su efecto exacto depende del bloque o condición de frontera que lo contiene.",
}

DIAGNOSTICS = {
    "CoCell": "Número de Courant local: diagnóstico numérico de severidad advectiva del paso de tiempo.",
    "coolingRate": "-dT/dt: valores positivos representan enfriamiento local.",
    "dTdt": "Derivada temporal local de la temperatura.",
    "dAlphaLdt": "Derivada temporal local de la fracción líquida.",
    "solidificationRate": "-d(alphaL)/dt: positivo cuando progresa la solidificación.",
    "energyAdvectiveFlux": "Flujo advectivo de energía por las caras; su integral superficial da potencia advectiva.",
    "heatFlux": "Flujo térmico/conductivo por las caras.",
    "energyFlux": "Diagnóstico de flujo total de energía.",
    "flowType": "Clasificación local de topología de flujo derivada del gradiente de velocidad.",
    "flowTopology": "Campo auxiliar del diagnóstico de topología de flujo.",
    "vorticity": "Rotacional de U; cuantifica movimiento local de rotación.",
    "gradT": "Gradiente vectorial de temperatura.",
    "magGradT": "Magnitud del gradiente de temperatura.",
    "gradRho": "Gradiente vectorial de densidad.",
    "magGradRho": "Magnitud del gradiente de densidad.",
    "latentHeat": "Valor de calor latente utilizado por los diagnósticos.",
    "latentHeatRateVol": "Tasa volumétrica de liberación/absorción de calor latente.",
    "magSqrDevGradU": "Diagnóstico de deformación asociado al gradiente de velocidad.",
    "pRghAcceleration": "Escala de aceleración reconstruida a partir del gradiente de p_rgh.",
    "magPRghAcceleration": "Magnitud de la aceleración asociada al gradiente de p_rgh.",
    "phaseChangeSolidFraction": "Fracción sólida diagnóstica, igual a 1-alphaL.",
    "phaseChangeDarcyCoeff": "Coeficiente de amortiguamiento Darcy reconstruido con alphaL, Cu y q.",
    "phaseChangeDarcySp": "Coeficiente implícito con signo del término Darcy.",
    "phaseChangeDarcyAcceleration": "Aceleración equivalente de resistencia Darcy.",
    "magPhaseChangeDarcyAcceleration": "Magnitud de la aceleración de resistencia Darcy.",
    "phaseChangeModelDeltaT": "Diferencia de temperatura usada por la reconstrucción de flotación del modelo de cambio de fase.",
    "phaseChangeBuoyancyAcceleration": "Aceleración de flotación reconstruida para diagnóstico.",
    "phaseChangeBuoyancySu": "Fuente explícita de flotación reconstruida a partir de rhoRef y la aceleración.",
    "magPhaseChangeBuoyancyAcceleration": "Magnitud de la aceleración de flotación reconstruida.",
    "phaseChangeDragToBuoyancy": "Razón entre resistencia Darcy y flotación.",
    "phaseChangeDragToPressure": "Razón entre resistencia Darcy y aceleración debida a p_rgh.",
}

def rel_source(path: Path):
    parts = path.parts
    if len(parts) < 2:
        return None
    if parts[0] in ("cases_controlled_buoyancy", "cases_buoyancy"):
        if len(parts) < 3:
            return None
        return Path(*parts[2:])
    if parts[0] == "cleanproy":
        return Path(*parts[1:])
    return None

def is_source(path: Path):
    rel = rel_source(path)
    if rel is None:
        return False
    parts = rel.parts
    if any(p in {"postProcessing", "logs", "polyMesh", "dynamicCode"} or p.startswith("processor") for p in parts):
        return False
    if any(re.fullmatch(r"\d+(?:\.\d+)?", p) and p != "0" for p in parts):
        return False
    if path.name.startswith("log.") or path.name in {"CASE_NOTES.md", "CASE_VARIANT.md"}:
        return False
    return (
        parts[0] in {"0", "constant", "system"}
        or path.name in {"Allrun", "Allclean"}
    )

def first_value(text, key):
    m = re.search(rf"^\s*{re.escape(key)}\s+([^;\n]+);", text, re.M)
    return re.sub(r"\s+", " ", m.group(1).strip()) if m else None

def patch_types(text):
    vals = re.findall(r"^\s*type\s+([^;\n]+);", text, re.M)
    ignore = {"volScalarField", "volVectorField", "surfaceScalarField", "surfaceVectorField"}
    out = []
    for v in vals:
        v = v.strip()
        if v not in ignore and v not in out:
            out.append(v)
    return out[:12]

def add_value(lines, text, key):
    value = first_value(text, key)
    if value is not None:
        explanation = VALUE_EXPLANATIONS.get(key, "parámetro del bloque; debe interpretarse con el modelo o BC que lo contiene.")
        lines.append(f"{key} = {value}: {explanation}")

def documentation(path, text):
    name = path.name
    lines = [
        f"Archivo documentado: {rel_source(path)}.",
        "El contenido ejecutable anterior permanece intacto; este apéndice solo explica su función e interacción con el modelo."
    ]

    if name == "Allrun":
        lines += [
            "FUNCIÓN: script que encadena preparación de malla/regiones, ejecución del solver y postprocesos configurados.",
            "INTERACCIÓN: el orden de comandos importa porque cada etapa consume archivos generados por la anterior. Los logs registran evidencia de ejecución sin modificar la física.",
            "Los argumentos de cada comando seleccionan caso, región, diccionario o tiempos; solo se convierten en parámetros físicos cuando la utilidad invocada lee esos valores desde un diccionario del modelo."
        ]
    elif name == "Allclean":
        lines += [
            "FUNCIÓN: elimina archivos generados para permitir reconstruir el caso desde las entradas originales.",
            "INTERACCIÓN: no cambia el modelo físico; 0/, constant/ y system/ siguen siendo la definición reproducible del siguiente cálculo."
        ]
    elif name == "controlDict":
        lines.append("FUNCIÓN: controla aplicación, intervalo temporal, paso de tiempo, escritura y ejecución de function objects.")
        for k in ("application","startFrom","startTime","endTime","deltaT","adjustTimeStep","maxCo","maxDeltaT","writeControl","writeInterval"):
            add_value(lines,text,k)
        lines.append("INTERACCIÓN: deltaT y maxCo afectan estabilidad temporal; writeControl/writeInterval determinan qué estados quedan disponibles para comparar perfiles y hacer postprocesamiento.")
    elif name == "fvSolution":
        lines += [
            "FUNCIÓN: define solvers lineales, tolerancias, precondicionadores y acoplamiento PIMPLE.",
            "Los bloques solvers{} actúan sobre campos concretos; tolerance fija el residuo absoluto objetivo y relTol permite detenerse respecto al residuo inicial.",
        ]
        for k in ("momentumPredictor","nOuterCorrectors","nCorrectors","nNonOrthogonalCorrectors","nEnergyCorrectors","pRefPoint","pRefValue"):
            add_value(lines,text,k)
        lines.append("INTERACCIÓN: PIMPLE controla cuánto se acoplan presión, velocidad y energía dentro de cada paso. pRefPoint/pRefValue fijan el datum de presión y deben interpretarse junto con p_rgh y pRef.")
    elif name == "fvSchemes":
        lines += [
            "FUNCIÓN: selecciona esquemas de discretización por volumen finito.",
            "ddtSchemes discretiza derivadas temporales; gradSchemes gradientes; divSchemes advección/divergencia; laplacianSchemes difusión; interpolationSchemes valores en caras; snGradSchemes gradientes normales.",
            "INTERACCIÓN: estos esquemas interactúan con calidad de malla y deltaT; pueden cambiar difusión numérica, oscilaciones y convergencia aun con propiedades físicas idénticas."
        ]
    elif name == "blockMeshDict":
        lines.append("FUNCIÓN: define escala geométrica, vértices, bloques, número de celdas y nombres de fronteras.")
        add_value(lines,text,"convertToMeters")
        lines += [
            "INTERACCIÓN: el tamaño de celda afecta resolución y Courant. Los nombres de patch deben coincidir con U, T, p_rgh y demás campos; de lo contrario las BC no se aplican al lugar esperado."
        ]
    elif name == "createZonesDict":
        lines += [
            "FUNCIÓN: identifica zonas de celdas/caras usadas para separar regiones o aplicar modelos.",
            "INTERACCIÓN: cambiar una selección puede mover celdas entre metal y molde aunque las propiedades termofísicas no cambien."
        ]
    elif name in {"functions","researchDiagnostics","lineProfiles","lineProfilesDict","momentumPostProcessing"}:
        lines += [
            "FUNCIÓN: configuración de diagnóstico/postprocesamiento; solicita campos, probes, perfiles o reducciones estadísticas.",
            "Los objetos diagnósticos aquí usados leen la solución y escriben resultados; no cambian las ecuaciones gobernantes."
        ]
        for k in ("executeControl","writeControl","writeInterval"):
            add_value(lines,text,k)
        lines += [
            "region selecciona la región de malla; fields los campos analizados; operation decide si se conservan valores espaciales o se reducen mediante suma/promedio/mínimo/máximo.",
            "INTERACCIÓN: las coordenadas de muestreo están en metros y deben corresponder con blockMesh. Para comparar casos deben coincidir ubicación y tiempos de escritura."
        ]
    elif name == "fvModels":
        lines.append("FUNCIÓN: activa fuentes/modelos volumétricos; en metal incluye cambio de fase, calor latente, resistencia Darcy de zona pastosa y, cuando aplica, flotación.")
        for k in ("Tsol","Tliq","L","Cu","q","beta","rhoRef","alpha1e","relax"):
            add_value(lines,text,k)
        lines.append("INTERACCIÓN: T modifica alphaL; alphaL controla calor latente y amortiguamiento Darcy; U modifica transporte convectivo de energía; la convección retroalimenta T y la solidificación.")
    elif name == "g":
        lines.append("FUNCIÓN: vector de aceleración gravitacional usado en flotación y corrección hidrostática.")
        add_value(lines,text,"value")
        lines.append("INTERACCIÓN: g entra en gh y por ello en p_rgh; dirección y magnitud definen la dirección y escala del término hidrostático/flotante.")
    elif name == "pRef":
        lines.append("FUNCIÓN: presión de referencia o datum de la formulación de presión.")
        add_value(lines,text,"value")
        lines.append("INTERACCIÓN: fija el nivel absoluto de referencia pero no crea por sí sola un gradiente; debe interpretarse con p, p_rgh, rho y g.")
    elif name == "momentumTransport":
        lines += [
            "FUNCIÓN: selecciona el modelo de transporte de momento/turbulencia.",
            "INTERACCIÓN: si el caso es laminar, campos como nut, k, epsilon u omega pueden permanecer como soporte/plantilla sin aportar transporte turbulento. Si se activa turbulencia, esos campos pasan a ser dinámicamente relevantes."
        ]
    elif name in {"castIron","silica","steel4140","steel4140cons"}:
        lines.append(f"FUNCIÓN: propiedades termofísicas del material {name}.")
        for k in ("rho0","beta","Cp","mu","kappa"):
            add_value(lines,text,k)
        lines += [
            "Las tablas dependientes de temperatura se interpolan entre pares temperatura-propiedad; el conjunto de filas representa una ley continua, no constantes aisladas.",
            "INTERACCIÓN: rho se acopla con gravedad/p_rgh; Cp y kappa controlan respuesta térmica; mu controla resistencia al flujo. En metal, todo ello retroalimenta el cambio de fase mediante T y alphaL."
        ]
    elif name == "physicalProperties":
        lines += [
            "FUNCIÓN: selecciona la formulación termofísica de la región y enlaza los modelos de propiedades.",
            "INTERACCIÓN: el modelo elegido determina cómo se interpretan densidad, energía, Cp, viscosidad y conductividad; cambiar el tipo de modelo puede cambiar el significado de los mismos números."
        ]
    elif name == "T":
        lines.append("FUNCIÓN: campo de temperatura y condiciones de frontera térmicas.")
        add_value(lines,text,"internalField")
        pts = patch_types(text)
        if pts:
            lines.append("Tipos de condición de frontera presentes: " + ", ".join(pts) + ".")
        lines += [
            "INTERACCIÓN: fixedValue impone T; condiciones de gradiente/flujo controlan transferencia; coupledTemperature intercambia calor entre regiones; resistencias de pared/air-gap modifican la ruta térmica metal-molde.",
            "T controla propiedades y fracción de fase, por lo que una BC térmica puede cambiar indirectamente densidad, flotación, U, calor latente y tiempo de solidificación."
        ]
    elif name == "U":
        lines.append("FUNCIÓN: campo de velocidad y condiciones cinemáticas.")
        add_value(lines,text,"internalField")
        pts = patch_types(text)
        if pts:
            lines.append("Tipos de condición de frontera presentes: " + ", ".join(pts) + ".")
        lines += [
            "INTERACCIÓN: noSlip fuerza velocidad nula; slip evita penetración normal y permite componente tangencial; empty representa la dirección inactiva de una geometría 2D/extruida.",
            "U transporta energía por convección, por lo que cambios de flujo pueden modificar enfriamiento y solidificación aun con las mismas propiedades."
        ]
    elif name == "p_rgh":
        lines.append("FUNCIÓN: presión modificada por flotación/hidrostática usada por el acoplamiento presión-momento.")
        add_value(lines,text,"internalField")
        pts = patch_types(text)
        if pts:
            lines.append("Tipos de condición de frontera presentes: " + ", ".join(pts) + ".")
        lines += [
            "INTERACCIÓN: p_rgh debe leerse junto con rho, g/gh y la referencia de presión. fixedFluxPressure ajusta el gradiente de presión para ser coherente con el flujo/velocidad; fixedValue impone p_rgh; prghPressure transforma una presión especificada a la forma p_rgh.",
            "La BC de presión puede cambiar phi y el transporte de masa/energía. sum(phi) cercano a cero puede ocultar entradas y salidas locales; para eso se revisa phi cara por cara o sumMag(phi)."
        ]
    elif name == "p":
        lines.append("FUNCIÓN: presión estática/termodinámica cuando la formulación la requiere.")
        add_value(lines,text,"internalField")
        pts = patch_types(text)
        if pts:
            lines.append("Tipos de condición de frontera presentes: " + ", ".join(pts) + ".")
        lines.append("INTERACCIÓN: en formulaciones con flotación, p y p_rgh están vinculadas por la corrección hidrostática y la referencia; tener las mismas dimensiones no significa que deban recibir el mismo valor numérico.")
    elif name == "phaseChangeSource:alpha1":
        lines.append("FUNCIÓN: fracción líquida del modelo de solidificación; aproximadamente 1 = líquido y 0 = sólido.")
        add_value(lines,text,"internalField")
        lines.append("INTERACCIÓN: alphaL controla calor latente y resistencia Darcy de la zona pastosa, enlazando energía y momento.")
    elif name in {"alphat","nut","k","epsilon","omega"}:
        lines.append(f"FUNCIÓN: campo auxiliar de transporte/turbulencia ({name}).")
        add_value(lines,text,"internalField")
        lines.append("INTERACCIÓN: su efecto depende del modelo seleccionado en momentumTransport; su mera presencia no implica que la turbulencia esté activa.")
    elif name in DIAGNOSTICS:
        lines.append("FUNCIÓN: " + DIAGNOSTICS[name])
        add_value(lines,text,"internalField")
        lines.append("INTERACCIÓN: es un campo de diagnóstico/interpretación y no modifica las ecuaciones salvo que otro modelo activo lo referencie explícitamente.")
    else:
        lines.append("FUNCIÓN: diccionario o campo auxiliar de OpenFOAM perteneciente a la configuración del caso.")
        add_value(lines,text,"internalField")
        pts = patch_types(text)
        if pts:
            lines.append("Tipos/modelos detectados: " + ", ".join(pts) + ".")
        lines.append("INTERACCIÓN: los valores deben interpretarse con sus dimensiones y con el bloque que los contiene; este comentario no altera ninguno de ellos.")

    lines.append("NOTA DE SEGURIDAD: todas las líneas de este apéndice son comentarios y no cambian la ejecución del caso.")
    return lines

def append_comments(path: Path):
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in raw:
        return False
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if MARKER in text:
        return False

    shell = path.name in {"Allrun","Allclean"} or text.startswith("#!")
    prefix = "# " if shell else "// "
    border = "# " + "="*76 if shell else "// " + "="*76
    lines = documentation(path, text)
    appendix = "\n" + border + "\n" + prefix + MARKER + "\n" + border + "\n"
    appendix += "\n".join(prefix + line for line in lines)
    appendix += "\n" + border + "\n"

    sep = "" if text.endswith("\n") else "\n"
    path.write_text(text + sep + appendix, encoding="utf-8")
    return True

def main():
    changed = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and is_source(path) and append_comments(path):
                changed.append(str(path))
    print(f"Annotated {len(changed)} case source files.")
    for p in changed:
        print(p)

if __name__ == "__main__":
    main()
