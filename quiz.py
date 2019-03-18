from cryptography.fernet import Fernet

key = 'TluxwB3fV_GWuLkR1_BzGs1Zk90TYAuhNMZP_0q4WyM='

# Oh no! The code is going over the edge! What are you going to do?
message = b'gAAAAABckCE_sLnR6SwelkkGJ1_roDbsCu_Vgk4K-LVTekJIVEOTywe1FHDm-p0L-KfUQvEHbuFgEZhCgMuFkb2kbFXY3xC3ZFVjRhPWc26BHGykhLQXm6G0ys6M-ea4cnR7E36_yMK8Kl-dbpuAnRGLm0aGt0b5qC7MY37S2JBQzRhYoq9HqNx9NRHqQCh3dkhfsIf8FNc4'

def main():
    f = Fernet(key)
    print(f.decrypt(message))

main()
