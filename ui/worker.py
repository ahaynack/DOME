# ui/worker.py
from PyQt5.QtCore import QObject, pyqtSignal
import traceback

class Module2Worker(QObject):
    """
    Worker thread for Mesostructure Generation.
    """
    finished = pyqtSignal()
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, controller, input_dict):
        super().__init__()
        self.controller = controller
        # Store parameters
        self.input_dict = input_dict

    def run(self):
        try:
            # Pass stored parameters to controller
            result = self.controller.execute_distribution(self.input_dict)
            
            if result:
                self.result_ready.emit(result)
        except Exception:
            print(traceback.format_exc())
            self.error_occurred.emit(traceback.format_exc())
        finally:
            self.finished.emit()

class SimulationWorker(QObject):
    """
    Worker thread for Surface Scaling Simulation.
    """
    finished = pyqtSignal()
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, controller, ui_inputs):
        super().__init__()
        self.controller = controller
        self.ui_inputs = ui_inputs

    def run(self):
        try:
            # Controller updates its internal state and runs logic
            result = self.controller.execute_simulation(self.ui_inputs)
            
            if result:
                self.result_ready.emit(result)
                
        except Exception:
            # Capture full traceback for debugging
            error_msg = traceback.format_exc()
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()