import numpy as np
import pandas as pd
import json



c = pd.read_csv('irt_track_out.csv',quotechar='"',index_col=False,skipinitialspace=True)
for col in c.select_dtypes(include=['object']).columns:
  c[col] = c[col].apply(lambda x: np.array(json.loads(x)))



