import numpy as np

SENSOR_NAMES = (
    [f"PS{i}" for i in range(1, 7)]
    + ["EPS1", "FS1", "FS2"]
    + [f"TS{i}" for i in range(1, 5)]
    + ["VS1", "CE", "CP"]
)

MUESTRAS_POR_SENSOR = {
    name: (6000 if name.startswith("PS") or name == "EPS1" else 600 if name.startswith("FS") else 60)
    for name in SENSOR_NAMES
}


def extraer_features_sensor(row):
    row = np.asarray(row, dtype=np.float64)
    q25, q75 = np.percentile(row, [25, 75])
    stats = [
        row.mean(),
        row.std(),
        row.min(),
        row.max(),
        np.sqrt(np.mean(np.square(row))),
        row.max() - row.min(),
        q25,
        q75,
    ]
    segment_means = [segment.mean() for segment in np.array_split(row, 10)]
    return stats + segment_means


def nombres_features():
    nombres = []
    for sensor in SENSOR_NAMES:
        nombres.extend([
            f"{sensor}_mean",
            f"{sensor}_std",
            f"{sensor}_min",
            f"{sensor}_max",
            f"{sensor}_rms",
            f"{sensor}_range",
            f"{sensor}_q25",
            f"{sensor}_q75",
        ])
        nombres.extend([f"{sensor}_seg_{i}_mean" for i in range(1, 11)])
    return nombres


FEATURE_NAMES = nombres_features()


def extraer_features(matrices):
    ciclos = matrices[SENSOR_NAMES[0]].shape[0]
    X = np.empty((ciclos, 288), dtype=np.float32)
    for ciclo in range(ciclos):
        fila = []
        for sensor in SENSOR_NAMES:
            fila.extend(extraer_features_sensor(matrices[sensor][ciclo]))
        X[ciclo] = fila
    return X
