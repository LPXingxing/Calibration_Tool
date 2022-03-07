#include <stdio.h>

#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#define uint32_t unsigned int
#define uint8_t unsigned char
#define unint_8 unsigned char


#define MAX_RADIAL_COEFFICIENTS 6
#define MAX_TANGENTIAL_COEFFICIENTS 2
#define MAX_FISHEYE_COEFFICIENTS 6


/**
* Extrinsic parameters shared by camera and IMU.
* All rotation + translation with respect to the same reference point
*/
struct extrinsics {     //24 bytes
	/**
	* Rotation parameter expressed in Rodrigues notation.
	* angle = sqrt(rx^2+ry^2+rz^2)
	* unit axis = [rx,ry,rz]/angle
	*/
	float rx, ry, rz;
	/**
	* Translation parameter from one camera to another parameter
	*/
	float tx, ty, tz;
};

/**
* Coefficients as per distortion model (wide FOV) being used.
*/
struct fisheye_lens_distortion_coeff {     //32 bytes
	/**
	* Radial coefficients count
	*/
	uint32_t coeff_count;     //4bytes
	/**
	* Radial coefficients
	*/
	float k[MAX_FISHEYE_COEFFICIENTS];   //24 bytes
	/**
	* 0 -> equidistant, 1 -> equisolid, 2 -> orthographic,
	* 3 -> stereographic
	*/
	uint32_t mapping_type;          //4bytes
};
/**
* Coefficients as per distortion model being used
*/
struct polynomial_lens_distortion_coeff {    //36 bytes
	/**
	* Radial coefficients count
	*/
	uint32_t radial_coeff_count;    //4 bytes
	/**
	* Radial coefficients
	*/
	float k[MAX_RADIAL_COEFFICIENTS];  //4*6 bytes
	/**
	* Tangential coefficients count
	*/
	uint32_t tangential_coeff_count;    //4 bytes
	/**
	* Tangential coefficients
	*/
	float p[MAX_TANGENTIAL_COEFFICIENTS]; //4*2 bytes
};
/**
* IMU parameters
*/
struct imu_params {    //60 bytes
	/**
	* 3D vector to add to accelerometer readings
	*/
	float linear_acceleration_bias[3];    //4*3 bytes
	/**
	* 3D vector to add to gyroscope readings
	*/
	float angular_velocity_bias[3];        //4*3 bytes
	/**
	* gravity acceleration
	*/
	float gravity_acceleration[3];        //4*3 bytes
	/**
	* Extrinsic structure for IMU device
	*/
	struct extrinsics extr;      //24 bytes
};



/**
* Camera Intrinsic parameters
*/
struct camera_intrinsics {
	/**
	* Width and height of image in pixels
	*/
	uint32_t width, height;    //4*2 bytes
	/**
	* Focal length in pixels    
	*/
	float fx, fy;                  //4*2 bytes
	/**
	* skew
	*/
	float skew;                  //4 bytes
	/**
	* Principal point (optical center) in pixels
	*/
	float cx, cy;                     //4*2 bytes
	/**
	* Structure for distortion coefficients as per the model being used
	* 0: pinhole, assuming polynomial distortion
	* 1: fisheye, assuming fisheye distortion)
	* 2: ocam (omini-directional)
	*/
	uint32_t distortion_type;    //4 bytes

	union distortion_coefficients   
	{
		struct polynomial_lens_distortion_coeff poly;     //36bytes
		struct fisheye_lens_distortion_coeff fisheye;    //32 bytes
	} dist_coeff;
};

/**
* Main structure for ISAAC parameters
*/
struct syncSensor_params {
	/**
	* EEPROM layout version
	*/
	uint32_t version;     //4
	/**
	* Factory Blob Flag, to set when factory flashed and reset to 0
	* when user modified
	*/
	int factory_data;  //4
	/**
	* Intrinsic structure for camera device
	*/
	struct camera_intrinsics left_cam_intr;  
	struct camera_intrinsics right_cam_intr;  
	/**
	* Extrinsic structure for camera device
	*/
	struct extrinsics cam_extr;
	/**
	* Flag for IMU 0-absent, 1-present
	*/
	unint_8 imu_present;
	/**
	* Intrinsic structure for IMU
	*/
	struct imu_params imu;
};

union eeprom_storage {
		struct syncSensor_params para;
		unsigned char s[256];
		
};


int main(int argc, void **argv)
{
    int tt;
    //for (tt=0; tt < argc; tt++)
    //    printf("Argument %d is %s.\n", tt, argv[tt]);
	
	float right_fx=atof(argv[1]);
	float right_fy=atof(argv[2]);
	float right_cx=atof(argv[3]);
	float right_cy=atof(argv[4]);
	float right_k1=atof(argv[5]);
	float right_k2=atof(argv[6]);
	float right_p1=atof(argv[7]);
	float right_p2=atof(argv[8]);
	float right_k3=atof(argv[9]);
	
	float right_k4=atof(argv[10]);
	float right_k5=atof(argv[11]);
	float right_k6=atof(argv[12]);
	
	
	float left_fx=atof(argv[13]);
	float left_fy=atof(argv[14]);
	float left_cx=atof(argv[15]);
	float left_cy=atof(argv[16]);
	float left_k1=atof(argv[17]);
	float left_k2=atof(argv[18]);
	float left_p1=atof(argv[19]);
	float left_p2=atof(argv[20]);
	float left_k3=atof(argv[21]);
	
	float left_k4=atof(argv[22]);
	float left_k5=atof(argv[23]);
	float left_k6=atof(argv[24]);
	
	float rx=atof(argv[25]);
	float ry=atof(argv[26]);
	float rz=atof(argv[27]);
	
	float tx=atof(argv[28]);
	float ty=atof(argv[29]);
	float tz=atof(argv[30]);
	
	char file_name[100];
	memset(file_name,0,100);
	strcpy(file_name,argv[31]);
	
	char camera_type[100];
	memset(camera_type,0,100);
	strcpy(camera_type,argv[32]);

	int pic_width=atoi(argv[33]);
	int pic_height=atoi(argv[34]);
	
	printf("write name=%s,camera_type=%s\n",file_name,camera_type);
	
	printf("eeprom parameter size = %ld \n",sizeof(struct syncSensor_params));
	struct extrinsics cam_extrin;
        	cam_extrin.rx = rx;
			cam_extrin.ry = ry;
			cam_extrin.rz = rz;
			cam_extrin.tx = tx;
			cam_extrin.ty = ty;
			cam_extrin.tz = tz;


	    struct fisheye_lens_distortion_coeff cam1_fieye_dist_coeff;
		cam1_fieye_dist_coeff.coeff_count=6;
		cam1_fieye_dist_coeff.k[0] = left_k1;
		cam1_fieye_dist_coeff.k[1] = left_k2;
		cam1_fieye_dist_coeff.k[2] = left_k3;
		cam1_fieye_dist_coeff.k[3] = left_k4;
		cam1_fieye_dist_coeff.k[4] = 0;
		cam1_fieye_dist_coeff.k[5] = 0;
		cam1_fieye_dist_coeff.mapping_type=0;
		

		struct polynomial_lens_distortion_coeff cam1_poly_dist_coeff;
			cam1_poly_dist_coeff.radial_coeff_count = 6;
			cam1_poly_dist_coeff.k[0] = left_k1;
			cam1_poly_dist_coeff.k[1] = left_k2;
			cam1_poly_dist_coeff.k[2] = left_k3;
			cam1_poly_dist_coeff.k[3] = left_k4;
			cam1_poly_dist_coeff.k[4] = left_k5;
			cam1_poly_dist_coeff.k[5] = left_k6;
			
			cam1_poly_dist_coeff.tangential_coeff_count = 2;
			cam1_poly_dist_coeff.p[0] = left_p1;
			cam1_poly_dist_coeff.p[1] = left_p2;

		struct polynomial_lens_distortion_coeff cam2_poly_dist_coeff;
			cam2_poly_dist_coeff.radial_coeff_count = 6;
			cam2_poly_dist_coeff.k[0] = right_k1;
			cam2_poly_dist_coeff.k[1] = right_k2;
			cam2_poly_dist_coeff.k[2] = right_k3;
			
			cam2_poly_dist_coeff.k[3] = right_k4;
			cam2_poly_dist_coeff.k[4] = right_k5;
			cam2_poly_dist_coeff.k[5] = right_k6;
			
			cam2_poly_dist_coeff.tangential_coeff_count = 2;
			cam2_poly_dist_coeff.p[0] = right_p1;
			cam2_poly_dist_coeff.p[1] = right_p2;

		struct camera_intrinsics cam1_intrinsics;
			cam1_intrinsics.width = pic_width;
			cam1_intrinsics.height = pic_height;
			cam1_intrinsics.fx = left_fx;
			cam1_intrinsics.fy = left_fy;
			cam1_intrinsics.cx = left_cx;
			cam1_intrinsics.cy = left_cy;
			cam1_intrinsics.skew = 0;
			if(strcmp(camera_type,"fisheye")==0)
			{
				cam1_intrinsics.distortion_type = 1;
				//cam1_intrinsics.dist_coeff.poly = cam1_poly_dist_coeff;	
				cam1_intrinsics.dist_coeff.fisheye = cam1_fieye_dist_coeff;
			}
			else{
				cam1_intrinsics.distortion_type = 0;
				cam1_intrinsics.dist_coeff.poly = cam1_poly_dist_coeff;
			}
			
		struct camera_intrinsics cam2_intrinsics;
			cam2_intrinsics.width = pic_width;
			cam2_intrinsics.height = pic_height;
			cam2_intrinsics.fx = right_fx;
			cam2_intrinsics.fy = right_fy;
			cam2_intrinsics.cx = right_cx;
			cam2_intrinsics.cy = right_cy;
			cam2_intrinsics.skew = 0;
			cam2_intrinsics.distortion_type = 0;
			cam2_intrinsics.dist_coeff.poly = cam2_poly_dist_coeff;


	struct imu_params hawk_imu_params = {0};
	/*hawk_imu_params.linear_acceleration_bias[0]=5.8996190401e-11;
	hawk_imu_params.linear_acceleration_bias[1]=1.09532295951e-12;
	hawk_imu_params.linear_acceleration_bias[2]=3.2338580353e-10;
	hawk_imu_params.angular_velocity_bias[0]=5.51560029394e-10;
	hawk_imu_params.angular_velocity_bias[1]=1.58478451231e-10;
	hawk_imu_params.angular_velocity_bias[2]=1.40991858188e-09;
	hawk_imu_params.gravity_acceleration[0]=5.74217814;
	hawk_imu_params.gravity_acceleration[1]=-7.94827338;
	hawk_imu_params.gravity_acceleration[2]=-0.14409511;
	*/
	
	//angular_velocity_bias
	//gravity_acceleration


	struct syncSensor_params hawk_param;
	hawk_param.version = 1;
	hawk_param.factory_data = 0;
	hawk_param.left_cam_intr = cam1_intrinsics;
	hawk_param.right_cam_intr = cam2_intrinsics;
	hawk_param.cam_extr = cam_extrin;
	hawk_param.imu_present = 1;
	hawk_param.imu = hawk_imu_params;


	union eeprom_storage eeprom_bin;
	unsigned char str[1024] =  {0};
	eeprom_bin.para=hawk_param;
	int i = 0;
	for(i = 0; i < 256; i++)
	{
		sprintf(str, "i2ctransfer -f -y 30 w2@0x%02x 0x%x 0x%x", 0x57+i/256, i&0xff, eeprom_bin.s[i]);
		printf("%s\n", str);
		usleep(5000);
		system(str);
	}
	FILE *fw = fopen(file_name, "wb");
    if (fw == NULL)
        return 0;
	 for (int i = 0; i < 256; i++)
	 {
        fwrite(eeprom_bin.s+i, sizeof(unsigned char), 1, fw);
        usleep(100);
	 }
	fclose(fw);
	
	printf("left_cam_intr.fx = 0x%x\n", *(int *)(&hawk_param.left_cam_intr.fx));
	return 0;
	
}
