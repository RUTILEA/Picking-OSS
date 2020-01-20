# Picking-OSS
Automatic picking module.



## Modules

### util

Common API for Robot operation.

### carrier

Allows you to carry an item by Robot with some end effector.

### picking

Picks up an item in bulk automatically.



## Development

#### Deployment

1. Clone the repository

   ```sh
   $ git clone git@github.com:RUTILEA/Picking-OSS.git
   ```

2. Move to the root directory

   ```sh
   $ cd Picking-OSS
   ```

3. Create a virtual environment in the project directory (Choose your own virtual environment name)

   ```sh
   $ python -m venv your_venv
   ```

4. Activate the virtual environment as your OS:
   - On Mac/Linux: `source your_venv/bin/activate`
   - On Windows: `your_venv\Scripts\activate.bat`

5. Install the required libraries.

   ```sh
   $ pip install -r requirements/base.txt -U
   ```

