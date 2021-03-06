import os
import sys
import time
import json
import socket
import subprocess


here = os.path.dirname(__file__)
datadir = os.path.join(here, '../data')

def get_emergent_version():
    """Get the version of the installed emergent"""
    output_str = subprocess.check_output(['emergent', '--version'])
    output_lines = output_str.decode('utf-8').split('\n')
    version_str = output_lines[0]
    assert version_str.startswith('Running ')
    version_str = version_str[8:]
    return version_str

emergent_version = get_emergent_version()


def write_desc(project_filename, output_filenames, datadir=datadir):
    generated_files = ', '.join(['`{}.dat`'.format(filename)
                                 for filename in output_filenames])
    print('Generated {}\n'.format(generated_files))

    for output_filename in output_filenames:
        with open(os.path.join(datadir, output_filename + '.md'), 'w') as f:
            s = ['`{}.dat`:'.format(output_filename),
                 '* generated from `{}` with **{}**.'.format(project_filename, emergent_version),
                 '']
            f.write('\n'.join(s))


class Emergent:

    def __init__(self, project_filename, verbose=True):
        """Open a project with a headless emergent"""
        self.project_filename = os.path.join(here, project_filename)
        self.verbose = verbose

        self.p = subprocess.Popen(['emergent', '-port', '5329','-nogui', '-server', '-p', self.project_filename])
#        self.p = subprocess.Popen(['emergent', '-server', '-p', self.project_filename])
        self.connect()

    def connect(self, tries=10):
        """Create a socket connected to the emergent instance"""
        while tries > 0:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect(('localhost', 5329))
                assert b'Emergent Server' in self.read_socket()
                return
            except ConnectionRefusedError:
                #print('refused ({})'.format(tries))
                time.sleep(1)
                tries -= 1
        raise ConnectionRefusedError

    def send(self, cmd, verbose=True):
        """Send a command to emergent a verify it went well."""
        if verbose:
            print('send: {}'.format(cmd))
        self.s.send(('{}\n'.format(json.dumps(cmd))).encode('utf-8'))
        #check status
        response = self.read_socket()
        response_json = json.loads(response.decode('utf-8'))
        if verbose:
            print('recv: {}'.format(response_json))
        assert response_json['status'] == 'OK', 'error: {}'.format(response_json)

    def read_socket(self):
        """Read all the data available on the socket"""
        data = b''
        part = self.s.recv(4096)
        data += part
        while len(part) == 4096: # QUESTION: what if it's *exactly* 4096?
            part = self.s.recv(4096)
            data += part
        return data

    def close(self):
        try:
            self.s.close()
        finally:
            self.p.kill() # using kill rather than terminate to avoid recovery file creation.


if __name__ == '__main__':
    run_cmd      = {'command': 'RunProgram', 'program': 'LeabraSettle'}
    filename_cmd = {'command': 'SetVar', 'program': 'SaveOutput', 'var_name': 'file_name', 'var_value': None}
    save_cmd     = {'command': 'RunProgram', 'program': 'SaveOutput'}

    # for adapt, output_filename, project_filename in [(False, 'neuron',       'neuron.proj'),
    #                                                  (True,  'neuron_adapt', 'neuron.proj')]:
    #     try:
    #         print('# Generating {}.dat'.format(output_filename))
    #         em = Emergent(project_filename)
    #         filename_cmd['var_value'] = os.path.join(datadir, output_filename)
    #
    #         em.send({'command': 'SetVar', 'program': 'SetAdapt', 'var_name': 'adapt_on', 'var_value': adapt})
    #         em.send({'command': 'RunProgram', 'program': 'SetAdapt'})
    #         em.send(run_cmd)
    #         em.send(filename_cmd)
    #         em.send(save_cmd)
    #
    #         write_desc(project_filename, [output_filename])
    #
    #     finally:
    #         em.close()
    #         time.sleep(2.0)
    #
    for inhib, output_filename, project_filename in [(False, 'neuron_pair',       'neuron_pair.proj'),
                                                     (True,  'neuron_pair_inhib', 'neuron_pair.proj')]:

        try:
            print('# Generating {}.dat'.format(output_filename))
            em = Emergent(project_filename)
            filename_cmd['var_value'] = os.path.join(datadir, output_filename)

            em.send({'command': 'SetVar', 'program': 'SetInhib', 'var_name': 'inhib_on', 'var_value': inhib})
            em.send({'command': 'RunProgram', 'program': 'SetInhib'})
            em.send({'command': 'RunProgram', 'program': 'LeabraTrain'})
            em.send(filename_cmd)
            em.send(save_cmd)

            write_desc(project_filename, [output_filename, output_filename + '_cycle'])

        finally:
            em.close()
            time.sleep(2.0)
    #
    #
    # ### layer_fffb.dat
    # output_filename  = 'layer_fffb'
    # project_filename = 'layer_fffb.proj'
    #
    # try:
    #     print('# Generating {}.dat'.format(output_filename))
    #     em = Emergent(project_filename)
    #     filename_cmd['var_value'] = os.path.join(datadir, output_filename)
    #
    #     em.send({'command': 'RunProgram', 'program': 'LeabraSettle'})
    #     em.send(filename_cmd)
    #     em.send(save_cmd)
    #
    #     write_desc(project_filename, [output_filename])
    #
    # finally:
    #     em.close()
    #     time.sleep(2.0)
    #
    #
    # ### netin.dat
    # output_filename  = 'netin'
    # project_filename = 'netin.proj'
    #
    # try:
    #     print('# Generating {}.dat'.format(output_filename))
    #     em = Emergent(project_filename)
    #     filename_cmd['var_value'] = os.path.join(datadir, output_filename)
    #
    #     em.send({'command': 'RunProgram', 'program': 'DeactivateQuarter'})
    #     em.send({'command': 'RunProgram', 'program': 'LeabraTrain'})
    #     em.send(filename_cmd)
    #     em.send(save_cmd)
    #
    #     write_desc(project_filename, [output_filename])
    #
    # finally:
    #     em.close()
    #     time.sleep(2.0)
    #
    #
    # ### leabra_std.dat
    # output_filename  = 'leabra_std'
    # project_filename = 'LeabraStd.proj'
    #
    # try:
    #     print('# Generating {}.dat'.format(output_filename))
    #     em = Emergent(project_filename)
    #     filename_cmd['var_value'] = os.path.join(datadir, output_filename)
    #
    #     em.send({'command': 'RunProgram', 'program': 'DeactivateQuarter'})
    #
    #     em.send({'command': 'RunProgram', 'program': 'LeabraTrain'})
    #     em.send(filename_cmd)
    #     em.send(save_cmd)
    #
    #     write_desc(project_filename, [output_filename, output_filename + '_cycle'])
    #
    #
    # finally:
    #     em.close()
    #     time.sleep(2.0)


    ### leabra_std4.dat and leabra_std25.dat
    for n in [4]:
        output_filename  = 'leabra_std{}'.format(n)
        project_filename = 'LeabraStd{}.proj'.format(n)

        try:
            print('# Generating {}.dat'.format(output_filename))
            em = Emergent(project_filename)
            filename_cmd['var_value'] = os.path.join(datadir, output_filename)

            em.send({'command': 'RunProgram', 'program': 'DeactivateQuarter'})

            em.send({'command': 'RunProgram', 'program': 'LeabraTrain'})
            em.send(filename_cmd)
            em.send(save_cmd)

            if n == 4:
                write_desc(project_filename, [output_filename, output_filename + '_cycle_hidden'])
                write_desc(project_filename, [output_filename, output_filename + '_cycle_output'])
            else:
                write_desc(project_filename, [output_filename, output_filename + '_cycle'])


        finally:
            em.close()
            time.sleep(2.0)
